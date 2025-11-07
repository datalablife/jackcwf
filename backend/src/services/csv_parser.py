"""
CSV file parser service for extracting and processing CSV data.

Provides functionality to parse CSV files, extract column information,
infer data types, and generate previews.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import csv
from dataclasses import dataclass


@dataclass
class ColumnInfo:
    """Information about a column in the CSV file."""

    name: str
    data_type: str  # "string", "integer", "float", "date", "boolean"
    sample_values: List[Any]


class CSVParserService:
    """
    Service for parsing CSV files.

    Provides methods to extract structure, infer types, and generate previews.
    """

    # Data type inference patterns
    EMPTY_VALUE_INDICATORS = {"", "null", "none", "na", "n/a", "unknown", "nan", "inf"}

    @staticmethod
    def parse_csv(file_path: str, encoding: str = "utf-8", delimiter: str = ",") -> Dict[str, Any]:
        """
        Parse a CSV file and extract its structure.

        Args:
            file_path: Path to the CSV file
            encoding: File encoding (default: utf-8)
            delimiter: Field delimiter (default: comma)

        Returns:
            Dictionary with file structure information

        Raises:
            Exception: If file cannot be parsed

        Example:
            >>> result = CSVParserService.parse_csv("data.csv")
            >>> result["row_count"]
            5000
        """
        try:
            with open(file_path, "r", encoding=encoding) as f:
                # Read all data
                reader = csv.DictReader(f, delimiter=delimiter)
                if not reader.fieldnames:
                    raise Exception("CSV file has no headers")

                rows = list(reader)

                if not rows:
                    return {
                        "row_count": 0,
                        "column_names": list(reader.fieldnames),
                        "data_types": [],
                        "columns_info": [],
                    }

                # Infer data types
                column_names = list(reader.fieldnames)
                data_types = CSVParserService._infer_data_types(rows, column_names)

                return {
                    "row_count": len(rows),
                    "column_names": column_names,
                    "data_types": data_types,
                    "columns_info": [
                        {
                            "name": col_name,
                            "data_type": data_type,
                        }
                        for col_name, data_type in zip(column_names, data_types)
                    ],
                }
        except Exception as e:
            raise Exception(f"Failed to parse CSV: {str(e)}")

    @staticmethod
    def get_column_names(file_path: str, encoding: str = "utf-8", delimiter: str = ",") -> List[str]:
        """
        Get column names from a CSV file.

        Args:
            file_path: Path to the CSV file
            encoding: File encoding (default: utf-8)
            delimiter: Field delimiter (default: comma)

        Returns:
            List of column names

        Example:
            >>> CSVParserService.get_column_names("data.csv")
            ["id", "name", "email", "age"]
        """
        try:
            with open(file_path, "r", encoding=encoding) as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                return list(reader.fieldnames) if reader.fieldnames else []
        except Exception as e:
            raise Exception(f"Failed to get column names: {str(e)}")

    @staticmethod
    def get_data_types(file_path: str, encoding: str = "utf-8", delimiter: str = ",") -> List[str]:
        """
        Infer data types from a CSV file.

        Args:
            file_path: Path to the CSV file
            encoding: File encoding (default: utf-8)
            delimiter: Field delimiter (default: comma)

        Returns:
            List of inferred data type strings

        Example:
            >>> CSVParserService.get_data_types("data.csv")
            ["integer", "string", "string", "integer"]
        """
        try:
            with open(file_path, "r", encoding=encoding) as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                rows = list(reader)
                column_names = list(reader.fieldnames) if reader.fieldnames else []
                return CSVParserService._infer_data_types(rows, column_names)
        except Exception as e:
            raise Exception(f"Failed to infer data types: {str(e)}")

    @staticmethod
    def get_preview(
        file_path: str,
        max_rows: int = 20,
        encoding: str = "utf-8",
        delimiter: str = ","
    ) -> Dict[str, Any]:
        """
        Get a preview of CSV file data.

        Args:
            file_path: Path to the CSV file
            max_rows: Maximum number of rows to return (default: 20)
            encoding: File encoding (default: utf-8)
            delimiter: Field delimiter (default: comma)

        Returns:
            Dictionary with preview data

        Example:
            >>> preview = CSVParserService.get_preview("data.csv")
            >>> len(preview["rows"])
            20
        """
        try:
            with open(file_path, "r", encoding=encoding) as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                column_names = list(reader.fieldnames) if reader.fieldnames else []

                rows = []
                for i, row in enumerate(reader):
                    if i >= max_rows:
                        break
                    rows.append(row)

                return {
                    "column_names": column_names,
                    "rows": rows,
                    "displayed_rows": len(rows),
                    "max_rows": max_rows,
                }
        except Exception as e:
            raise Exception(f"Failed to get preview: {str(e)}")

    @staticmethod
    def get_row_count(file_path: str, encoding: str = "utf-8", delimiter: str = ",") -> int:
        """
        Get the total number of rows in a CSV file.

        Args:
            file_path: Path to the CSV file
            encoding: File encoding (default: utf-8)
            delimiter: Field delimiter (default: comma)

        Returns:
            Number of data rows (excluding header)

        Example:
            >>> CSVParserService.get_row_count("data.csv")
            5000
        """
        try:
            with open(file_path, "r", encoding=encoding) as f:
                reader = csv.DictReader(f, delimiter=delimiter)
                return sum(1 for _ in reader)
        except Exception as e:
            raise Exception(f"Failed to count rows: {str(e)}")

    @staticmethod
    def _infer_data_types(rows: List[Dict[str, Any]], column_names: List[str]) -> List[str]:
        """
        Infer data types for columns based on sample data.

        Args:
            rows: List of data rows
            column_names: List of column names

        Returns:
            List of inferred data type strings

        Inference rules:
        - All non-numeric: string
        - All numeric integers: integer
        - Mix of integers and floats: float
        - Contains datetime patterns: datetime
        - Mix of True/False/Yes/No: boolean
        """
        data_types = []

        for col_name in column_names:
            col_type = CSVParserService._infer_column_type(rows, col_name)
            data_types.append(col_type)

        return data_types

    @staticmethod
    def _infer_column_type(rows: List[Dict[str, Any]], column_name: str) -> str:
        """Infer the data type of a single column."""
        if not rows:
            return "string"

        # Sample first 100 non-empty values
        sample_values = []
        for row in rows[:100]:
            value = row.get(column_name, "")
            if value and str(value).lower() not in CSVParserService.EMPTY_VALUE_INDICATORS:
                sample_values.append(str(value).strip())

        if not sample_values:
            return "string"

        # Try to infer type
        all_int = True
        all_float = True
        all_bool = True

        for val in sample_values:
            # Check boolean
            if val.lower() not in {"true", "false", "yes", "no", "1", "0"}:
                all_bool = False

            # Check integer
            try:
                int(val)
            except ValueError:
                all_int = False

            # Check float
            try:
                float(val)
            except ValueError:
                all_float = False

        if all_bool:
            return "boolean"
        elif all_int:
            return "integer"
        elif all_float:
            return "float"
        else:
            return "string"
