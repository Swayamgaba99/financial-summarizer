import os
import logging
import pandas as pd
from typing import List, Dict
from llama_index.core import VectorStoreIndex, load_index_from_storage, StorageContext
from ragas.metrics import answer_relevancy, faithfulness, context_recall
from ragas import evaluate
from langchain_openai import OpenAI
from datasets import Dataset

logger = logging.getLogger(__name__)

class RagaEvaluator:
    def __init__(self, vector_dir: str, ground_truth: List[Dict],  openai_api_key: str):
        self.vector_dir = vector_dir
        self.ground_truth = ground_truth
        self.index = self._load_index()
        os.environ["OPENAI_API_KEY"] = openai_api_key
        self.llm = OpenAI(api_key=openai_api_key)

    def _load_index(self) -> VectorStoreIndex:
        logger.info("Loading vector index from storage")
        try:
            storage_context = StorageContext.from_defaults(persist_dir=self.vector_dir)
            return load_index_from_storage(storage_context)
        except Exception as e:
            logger.error(f"Index loading failed: {str(e)}")
            raise

    def _prepare_dataset(self) -> Dataset:
        questions = []
        answers = []
        contexts = []
        references = []

        query_engine = self.index.as_query_engine()

        for qa in self.ground_truth:
            try:
                response = query_engine.query(qa["question"])
                questions.append(qa["question"])
                answers.append(str(response))
                references.append(qa["answer"])
                contexts.append([n.node.text for n in response.source_nodes])
            except Exception as e:
                logger.error(f"Query failed for '{qa['question']}': {str(e)}")
                continue

        return Dataset.from_dict({
            "question": questions,
            "answer": answers,
            "contexts": contexts,
            "reference": references
        })

    def run_evaluation(self) -> pd.DataFrame:
        logger.info("Running RAGAS evaluation")
        dataset = self._prepare_dataset()

        result = evaluate(
            dataset,
            metrics=[answer_relevancy, faithfulness, context_recall],
        )

        return result.to_pandas()