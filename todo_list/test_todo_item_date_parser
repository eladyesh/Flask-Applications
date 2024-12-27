import pytest


class TodoItemDateParser:
    def __init__(self):
        # Complex initialization logic
        print("TodoItemDateParser initialized")

    def parse_date(self, date_str):
        # Imagine this does some complex date parsing
        return f"Parsed: {date_str}"


class BasicTodoItemStrategy:
    def __init__(self):
        self.date_parser = TodoItemDateParser()

    def process_date(self, date_str):
        return self.date_parser.parse_date(date_str)


@pytest.fixture
def mock_date_parser(mocker):
    mocker.patch.object(TodoItemDateParser, '__init__', return_value=None)
    mock_parse_date = mocker.patch.object(TodoItemDateParser, 'parse_date')
    return mock_parse_date


def test_process_date(mock_date_parser):
    # Create an instance of BasicTodoItemStrategy
    strategy = BasicTodoItemStrategy()

    # Call the process_date method
    result = strategy.process_date("2024-12-27")

    # Verify that the mocked parse_date method was called
    mock_date_parser.assert_called_once_with("2024-12-27")
