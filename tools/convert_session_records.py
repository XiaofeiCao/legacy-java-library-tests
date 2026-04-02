"""Convert legacy azure-libraries-for-java session records to TestProxy format.

Old format:
{
  "networkCallRecords": [{"Method", "Uri", "Headers", "Response"}],
  "variables": ["val1", "val2", ...]
}

New format:
{
  "Entries": [{"RequestUri", "RequestMethod", "RequestHeaders", "RequestBody", "StatusCode", "ResponseHeaders", "ResponseBody"}],
  "Variables": {"0": "val1", "1": "val2", ...}
}

In the old format, Response is a flat dict mixing:
  - "StatusCode" (string) -> int
  - "Body" (string) -> ResponseBody
  - everything else -> ResponseHeaders
"""
import json
import sys
import os

def convert_record(old_record):
    """Convert a single networkCallRecord to a TestProxy Entry."""
    entry = {
        "RequestUri": old_record.get("Uri", ""),
        "RequestMethod": old_record.get("Method", ""),
        "RequestHeaders": old_record.get("Headers", {}),
        "RequestBody": None,
    }

    response = old_record.get("Response", {})

    status_code = int(response.get("StatusCode", 200))
    body = response.get("Body", "")
    
    # Everything except StatusCode and Body is a response header
    response_headers = {}
    for k, v in response.items():
        if k not in ("StatusCode", "Body"):
            response_headers[k] = v

    entry["StatusCode"] = status_code
    entry["ResponseHeaders"] = response_headers
    entry["ResponseBody"] = body

    return entry

def convert_file(input_path, output_path):
    """Convert a full session record file."""
    with open(input_path, 'r') as f:
        old_data = json.load(f)

    entries = [convert_record(r) for r in old_data.get("networkCallRecords", [])]

    old_vars = old_data.get("variables", [])
    variables = {str(i): v for i, v in enumerate(old_vars)}

    new_data = {
        "Entries": entries,
        "Variables": variables
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(new_data, f, indent=2)
    
    print(f"  Converted: {os.path.basename(input_path)} ({len(entries)} entries, {len(variables)} variables)")

def main():
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} <input_dir> <output_dir>")
        sys.exit(1)
    
    input_dir = sys.argv[1]
    output_dir = sys.argv[2]
    
    for filename in sorted(os.listdir(input_dir)):
        if filename.endswith('.json'):
            convert_file(
                os.path.join(input_dir, filename),
                os.path.join(output_dir, filename)
            )

if __name__ == "__main__":
    main()
