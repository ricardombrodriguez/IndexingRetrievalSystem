"""
Authors:
Gonçalo Leal - 98008
Ricardo Rodriguez - 98388
"""

class MetricsCalcultor:
    """
    Helper class to calculate the metrics of a query (exercise 3)
    """
    @staticmethod
    def calculate_recall(obtained_docs, relevant_docs):
        """
        Calculate the recall of a query.

        recall = number of relevant docs in obtained docs / number of relevant docs

        Input:
            obtained_docs: list of documents returned by theobtained query
            relevant_docs: list of relevant documents for the query
        """
        return len(set(obtained_docs).intersection(set(relevant_docs))) / len(relevant_docs)

    @staticmethod
    def calculate_precision(obtained_docs, relevant_docs):
        """
        Calculate the precision of a query.

        precision = number of relevant docs in obtained docs / number of obtained docs

        Input:
            obtained_docs: list of documents returned by the query
            relevant_docs: list of relevant documents for the query
        """
        return len(set(obtained_docs).intersection(set(relevant_docs))) / len(obtained_docs)

    @staticmethod
    def calculate_fmeasure(obtained_docs, relevant_docs):
        """
        Calculate the f-measure of a query.

        f-measure = 2 * (precision * recall) / (precision + recall)

        Nota:   se o input fosse já o valor do recall e da precision
                este método seria mais eficiente, mas não seria tão transparente

        Input:
            obtained_docs: list of documents returned by the query
            relevant_docs: list of relevant documents for the query
        """
        recall = MetricsCalcultor.calculate_recall(obtained_docs, relevant_docs)
        precision = MetricsCalcultor.calculate_precision(obtained_docs, relevant_docs)

        # careful with division by zero errors
        if precision + recall == 0:
            return 0

        return 2 * (precision * recall) / (precision + recall)

    @staticmethod
    def calculate_average_precision(obtained_docs, relevant_docs):
        """
        Calculate the average precision of a query.

        average precision = sum(precision at each relevant document) / number of relevant documents

        Input:
            obtained_docs: list of documents returned by the query
            relevant_docs: list of relevant documents for the query
        """
        precision_sum = 0
        for i, doc in enumerate(obtained_docs):
            if doc in relevant_docs:
                # calculate precision at each relevant document
                # [:i+1] because we want to include the current document
                # slicing in python is exclusive :( so we need to add 1
                precision_sum += MetricsCalcultor.calculate_precision(
                    obtained_docs[:i+1], relevant_docs
                )

        return precision_sum / len(relevant_docs)
