import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io
import cv2
import tabula
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
import logging
from pathlib import Path
from typing import List, Any, Dict, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import base64
import openai

logger = logging.getLogger(__name__)


class PDFLoader:
    """
    Loads and processes PDF files with parallel extraction and GPT-4 image summaries.
    """

    def __init__(self, input_dir: str, openai_api_key: str):
        self.input_dir = input_dir
        self.openai_api_key = openai_api_key  # Store the API key
        self.pdf_files: List[Path] = []
        self.documents: List[Document] = []
        self.image_summary: Dict[str, int] = {}
        self.tables: List[Tuple[str, pd.DataFrame]] = []  # To store (name, DataFrame) tuples

    def load_pdfs(self) -> List[Document]:
        """
        Load and process all PDF files in the input directory.
        """

        start_time = time.time()
        self.pdf_files = list(Path(self.input_dir).glob("*.pdf"))
        if not self.pdf_files:
            raise ValueError(f"No PDF files found in {self.input_dir}")
        logger.info(f"Found {len(self.pdf_files)} PDF files")

        for pdf_path in self.pdf_files:
            self._process_pdf(pdf_path)

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=300, separators=["\n\n", "\n", ".", ",", " ", ""]
        )
        split_docs = text_splitter.split_documents(self.documents)

        # Vector store creation moved out of _process_pdf
        # self.vector_store = FAISS.from_documents(split_docs, self.embeddings) # Assuming self.embeddings is set elsewhere

        logger.info(f"Processed {len(self.pdf_files)} PDFs into {len(split_docs)} chunks")
        logger.info(f"Total processing time: {time.time() - start_time:.2f} seconds")  # Log total time
        return split_docs

    def _process_pdf(self, pdf_path: Path):
        """
        Process a single PDF file using a thread pool for parallel extraction.
        """

        start_time = time.time()
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = {
                executor.submit(self._extract_text, pdf_path): "text",
                executor.submit(self._extract_tables, pdf_path): "table",
                executor.submit(self._extract_images, pdf_path): "image",
            }

            for future in as_completed(futures):
                try:
                    future.result()  # Get the result (or exception if one occurred)
                except Exception as e:
                    logger.error(f"Extraction task failed: {e}")

        # self._extract_source_facts("\n".join([doc.page_content for doc in self.documents])) # You might need this later
        logger.info(f"Total extraction time for {pdf_path.name}: {time.time() - start_time:.1f}s")

    def _extract_text(self, pdf_path: Path):
        """
        Extract text from PDF using PyMuPDF.
        """

        try:
            loader = PyMuPDFLoader(str(pdf_path))
            docs = loader.load()
            for doc in docs:
                doc.metadata["source_type"] = "text"
                doc.metadata["filename"] = pdf_path.name
            self.documents.extend(docs)
            logger.info(f"Extracted {len(docs)} text pages from {pdf_path.name}")
        except Exception as e:
            logger.error(f"Error extracting text from {pdf_path.name}: {str(e)}")

    def _extract_tables(self, pdf_path: Path):
        """
        Extract tables from PDF using tabula.
        """

        try:
            try:
                tabula_tables = tabula.read_pdf(
                    str(pdf_path), pages="all", multiple_tables=True, pandas_options={"header": None}
                )
                if tabula_tables:
                    logger.info(f"Extracted {len(tabula_tables)} tables using tabula from {pdf_path.name}")
                    for i, table in enumerate(tabula_tables):
                        if not table.empty:
                            table_text = table.to_string()
                            doc = Document(
                                page_content=f"TABLE {i + 1}:\n{table_text}",
                                metadata={
                                    "source": str(pdf_path),
                                    "source_type": "table",
                                    "table_id": i,
                                    "filename": pdf_path.name,
                                },
                            )
                            self.documents.append(doc)
                            self.tables.append((f"{pdf_path.name}_table_{i}", table))
                else:
                    logger.info(f"No tables found in {pdf_path.name} using tabula")
            except Exception as e:
                logger.warning(f"Tabula extraction failed for {pdf_path.name}: {str(e)}")
        except Exception as e:
            logger.error(f"Error extracting tables from {pdf_path.name}: {str(e)}")

    def _extract_images(self, pdf_path: Path):
        """
        Extract images from PDF, get GPT-4 summaries, and store as Documents.
        """

        try:
            doc = fitz.open(str(pdf_path))
            seen_xrefs = set()  # To avoid duplicate image extraction
            image_count = 0

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                image_list = page.get_images(full=True)

                for img in image_list:
                    xref = img[0]
                    if xref in seen_xrefs:
                        continue  # Skip duplicate image
                    seen_xrefs.add(xref)

                    try:
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        width = base_image["width"]
                        height = base_image["height"]

                        if width >= 100 and height >= 100:  # Basic size filter
                            base64_image = base64.b64encode(image_bytes).decode("utf-8")
                            try:
                                response = openai.chat.completions.create(
                                    model="gpt-4o",  # Or your preferred model
                                    api_key=self.openai_api_key,  # Use the stored API key
                                    messages=[
                                        {
                                            "role": "user",
                                            "content": [
                                                {
                                                    "type": "text",
                                                    "text": "Give a concise summary of the graph or chart shown with all the numerical data in this image.",
                                                },
                                                {
                                                    "type": "image_url",
                                                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                                                },
                                            ],
                                        }
                                    ],
                                    max_tokens=100,
                                )
                                summary = response.choices[0].message.content.strip()

                                img_doc = Document(
                                    page_content=f"IMAGE SUMMARY (Page {page_num + 1}, Image {image_count + 1}):\n{summary}",
                                    metadata={
                                        "source": str(pdf_path),
                                        "source_type": "image",
                                        "page_num": page_num,
                                        "image_id": xref,
                                        "filename": pdf_path.name,
                                        "width": width,
                                        "height": height,
                                    },
                                )
                                self.documents.append(img_doc)
                                image_count += 1
                            except Exception as e_openai:
                                logger.warning(
                                    f"GPT-4 summary failed (pg {page_num + 1}, xref {xref}) in {pdf_path.name}: {e_openai}"
                                )
                        else:
                            logger.info(
                                f"Skipping small image (pg {page_num + 1}, xref {xref}) in {pdf_path.name}: width={width}, height={height}"
                            )

                    except Exception as e_extract:
                        logger.warning(
                            f"Skipping image (pg {page_num + 1}, xref {xref}) in {pdf_path.name}: {str(e_extract)}"
                        )

            logger.info(f"Extracted and summarized {image_count} images from {pdf_path.name}")
            self.image_summary[pdf_path.name] = image_count  # Update image summary
        except Exception as e:
            logger.error(f"Error processing images from {pdf_path.name}: {str(e)}")