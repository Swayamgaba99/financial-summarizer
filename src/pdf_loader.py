import os
from pathlib import Path
from typing import List, Union
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import base64
import openai  
from collections import defaultdict
from datetime import datetime

from langchain.chat_models import ChatOpenAI
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.schema import Document, HumanMessage
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS

import fitz  # 
import tabula
from langchain.document_loaders import PyMuPDFLoader  # For text
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PDFProcessor:
    """
    A class to load, process PDF files from a directory, store the extracted information,
    split it into chunks, and create a vector store.
    """

    def __init__(self, input_dir: str):
        """
        Initialize the PDF processor.

        Args:
            input_dir: Directory containing input PDF files
        """
        self.input_dir = input_dir
        self.pdf_files: List[Path] = []
        self.documents: List[Document] = []
        self.vector_store: FAISS = None  
        self.embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'} 
        )

        self.load_pdfs()  # Process PDFs in the input directory

    def load_pdfs(self):
        """Load and process all PDF files in the input directory."""
        start_time = time.time()
        self.pdf_files = list(Path(self.input_dir).glob("*.pdf"))
        if not self.pdf_files:
            raise ValueError(f"No PDF files found in {self.input_dir}")
        logger.info(f"Found {len(self.pdf_files)} PDF files")

        for pdf_path in self.pdf_files:
            self._process_pdf(pdf_path)

        # Create text splitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=300,
            separators=["\n\n", "\n", ".", ",", " ", ""]
        )

        # Split documents
        split_docs = text_splitter.split_documents(self.documents)

        # Create vector store
        self.vector_store = FAISS.from_documents(split_docs, self.embeddings)

        logger.info(f"Processed {len(self.pdf_files)} PDFs into {len(split_docs)} chunks")
        logger.info(f"Total time to load and process PDFs: {time.time() - start_time:.1f}s")

    def _process_pdf(self, pdf_path: Path):
        """
        Processes a single PDF file to extract text, tables, and images.

        Args:
            pdf_path (Path): Path to the PDF file.
        """
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(self._extract_text, pdf_path): "text",
                executor.submit(self._extract_tables, pdf_path): "table",
                executor.submit(self._extract_images, pdf_path): "image",
            }
            for fut in as_completed(futures):
                fut.result()  # Ensure exceptions are raised and logged

        logger.info(f"Time to process {pdf_path.name}: {time.time() - start_time:.1f}s")

    def _extract_text(self, pdf_path: Path):
        """Extract text from PDF using PyMuPDF."""
        try:
            loader = PyMuPDFLoader(str(pdf_path))
            docs = loader.load()

            # Add metadata to track source
            for doc in docs:
                doc.metadata["source_type"] = "text"
                doc.metadata["filename"] = pdf_path.name

            self.documents.extend(docs)
            logger.info(f"Extracted {len(docs)} text pages from {pdf_path.name}")
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path.name}: {str(e)}")

    def _extract_tables(self, pdf_path: Path):
        """Extract tables from PDF using tabula."""
        try:
            # Use tabula for table extraction
            try:
                tabula_tables = tabula.read_pdf(
                    str(pdf_path),
                    pages='all',
                    multiple_tables=True,
                    pandas_options={'header': None}
                )

                if tabula_tables:
                    logger.info(f"Extracted {len(tabula_tables)} tables using tabula from {pdf_path.name}")

                    for i, table in enumerate(tabula_tables):
                        if not table.empty:
                            table_text = table.to_string()
                            doc = Document(
                                page_content=f"TABLE {i+1}:\n{table_text}",
                                metadata={
                                    "source": str(pdf_path),
                                    "source_type": "table",
                                    "table_id": i,
                                    "filename": pdf_path.name
                                }
                            )
                            self.documents.append(doc)

            except Exception as e:
                logger.warning(f"Tabula extraction failed for {pdf_path.name}: {str(e)}")

        except Exception as e:
            logger.error(f"Error extracting tables from {pdf_path.name}: {str(e)}")


    def _extract_images(self, pdf_path: Path):
      """Extract images from PDF, get GPT-4 summaries, and store as Documents without saving to disk."""
      try:
          doc = fitz.open(str(pdf_path))
          seen_xrefs = set()
          image_count = 0

          for page_num in range(len(doc)):
              page = doc.load_page(page_num)
              image_list = page.get_images(full=True)

              for img in image_list:
                  xref = img[0]
                  if xref in seen_xrefs:
                      continue
                  seen_xrefs.add(xref)

                  try:
                      base_image = doc.extract_image(xref)
                      image_bytes = base_image["image"]
                      width = base_image["width"]
                      height = base_image["height"]

                      if width >= 100 and height >= 100:
                          # Process image directly from memory
                          base64_image = base64.b64encode(image_bytes).decode('utf-8')

                          response = openai.chat.completions.create(
                              model="gpt-4o",
                              messages=[
                                  {
                                      "role": "user",
                                      "content": [
                                          {
                                              "type": "text",
                                              "text": "Give a concise summary of the graph or chart shown with all the numerical data in this image."
                                          },
                                          {
                                              "type": "image_url",
                                              "image_url": {
                                                  "url": f"data:image/jpeg;base64,{base64_image}"
                                              }
                                          }
                                      ]
                                  }
                              ],
                              max_tokens=100
                          )

                          summary = response.choices[0].message.content.strip()

                          # Create Document object
                          img_doc = Document(
                              page_content=f"IMAGE SUMMARY (Page {page_num+1}, Image {image_count+1}):\n{summary}",
                              metadata={
                                  "source": str(pdf_path),
                                  "source_type": "image",
                                  "page_num": page_num,
                                  "image_id": xref,
                                  "filename": pdf_path.name,
                                  "width": width,
                                  "height": height
                              }
                          )

                          self.documents.append(img_doc)
                          image_count += 1

                  except Exception as e:
                      logger.warning(f"Skipping image (pg {page_num+1}, xref {xref}) in {pdf_path.name}: {str(e)}")

          logger.info(f"Extracted and summarized {image_count} images from {pdf_path.name}")

      except Exception as e:
          logger.error(f"Error processing images from {pdf_path.name}: {str(e)}")