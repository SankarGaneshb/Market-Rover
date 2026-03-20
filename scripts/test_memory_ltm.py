import json
import datetime
from rover_tools.memory_tool import evaluate_pending_predictions, read_memory, write_memory

def test_ltm():
    memory = read_memory()
    
    past_date = (datetime.date.today() - datetime.timedelta(days=14)).isoformat()
    mock_entry = {
        "date": past_date,
        "ticker": "RELIANCE.NS",
        "signal": "buy",
        "confidence": "High",
        "outcome": "Pending"
    }
    
    memory.append(mock_entry)
    write_memory(memory)
    
    print("Mock memory added.")
    print("Before Evaluation:", [m for m in read_memory() if m.get("ticker") == "RELIANCE.NS" and m.get("date") == past_date])
    
    print("\nRunning Evaluator...")
    evaluate_pending_predictions()
    
    print("\nAfter Evaluation:", [m for m in read_memory() if m.get("ticker") == "RELIANCE.NS" and m.get("date") == past_date])

if __name__ == "__main__":
    test_ltm()
