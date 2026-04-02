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

TestProxy naming convention:
  - Legacy: methodName.json (e.g., canCRUDVault.json)
  - TestProxy: ClassName.methodName.json (e.g., VaultTests.canCRUDVault.json)
  When --test-dir is provided, output files are renamed with the class prefix.
"""
import json
import sys
import os
import re
import argparse


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
    
    print(f"  Converted: {os.path.basename(input_path)} -> {os.path.basename(output_path)} ({len(entries)} entries, {len(variables)} variables)")


def build_method_class_map(test_dir):
    """Scan Java test files to build a mapping of method name -> class name.
    
    Looks for @Test-annotated methods (excluding @Ignore) and maps each
    method name to its containing class, enabling ClassName.methodName.json
    naming for TestProxy session records.
    """
    method_map = {}
    class_pattern = re.compile(r'public\s+class\s+(\w+)')
    test_annotation = re.compile(r'@Test\b')
    ignore_annotation = re.compile(r'@Ignore\b')
    method_pattern = re.compile(r'public\s+void\s+(\w+)\s*\(')

    for root, _, files in os.walk(test_dir):
        for fname in files:
            if not fname.endswith('.java'):
                continue
            filepath = os.path.join(root, fname)
            with open(filepath, 'r') as f:
                lines = f.readlines()

            current_class = None
            for i, line in enumerate(lines):
                class_match = class_pattern.search(line)
                if class_match:
                    current_class = class_match.group(1)

                if test_annotation.search(line) and current_class:
                    # Check if @Ignore appears on the same line or adjacent lines
                    context = ''.join(lines[max(0, i-2):i+1])
                    if ignore_annotation.search(context):
                        continue
                    # Find the method declaration in the next few lines
                    for j in range(i, min(i + 5, len(lines))):
                        method_match = method_pattern.search(lines[j])
                        if method_match:
                            method_name = method_match.group(1)
                            method_map[method_name] = current_class
                            break

    return method_map


def main():
    parser = argparse.ArgumentParser(
        description='Convert legacy session records to TestProxy format.')
    parser.add_argument('input_dir', help='Directory with legacy session record JSON files')
    parser.add_argument('output_dir', help='Directory for converted TestProxy format files')
    parser.add_argument('--test-dir',
                        help='Java test source directory to scan for method->class mapping. '
                             'When provided, output files are named ClassName.methodName.json '
                             'instead of just methodName.json (TestProxy convention).')
    args = parser.parse_args()

    method_map = {}
    if args.test_dir:
        method_map = build_method_class_map(args.test_dir)
        if method_map:
            print(f"  Built method->class mapping ({len(method_map)} methods):")
            for method, cls in sorted(method_map.items()):
                print(f"    {method} -> {cls}")
        else:
            print("  Warning: no @Test methods found, using original file names")

    for filename in sorted(os.listdir(args.input_dir)):
        if not filename.endswith('.json'):
            continue

        method_name = filename[:-5]  # strip .json
        if method_map and method_name in method_map:
            out_filename = f"{method_map[method_name]}.{method_name}.json"
        else:
            out_filename = filename

        convert_file(
            os.path.join(args.input_dir, filename),
            os.path.join(args.output_dir, out_filename)
        )


if __name__ == "__main__":
    main()
