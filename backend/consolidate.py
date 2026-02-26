import os
from datetime import datetime
from backend.config import PROCESSED_DIR, DATA_DIR

def consolidate_documents(output_filename: str = "consolidated_documents.txt") -> str:
    """
    Consolidate all processed text files into a single document.
    
    Args:
        output_filename: Name of the output file (default: consolidated_documents.txt)
    
    Returns:
        Path to the consolidated document
    """
    output_path = os.path.join(DATA_DIR, output_filename)
    
    if not os.path.exists(PROCESSED_DIR):
        print(f"Processed directory not found: {PROCESSED_DIR}")
        return None
    
    # Get all .txt files from processed directory
    txt_files = sorted([f for f in os.listdir(PROCESSED_DIR) if f.endswith('.txt')])
    
    if not txt_files:
        print("No processed text files found to consolidate.")
        return None
    
    print(f"Consolidating {len(txt_files)} documents...")
    print("=" * 60)
    
    total_chars = 0
    
    with open(output_path, 'w', encoding='utf-8') as outfile:
        # Write header
        outfile.write("=" * 80 + "\n")
        outfile.write("CONSOLIDATED DOCUMENT COLLECTION\n")
        outfile.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        outfile.write(f"Total Documents: {len(txt_files)}\n")
        outfile.write("=" * 80 + "\n\n")
        
        # Process each file
        for idx, filename in enumerate(txt_files, 1):
            file_path = os.path.join(PROCESSED_DIR, filename)
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as infile:
                    content = infile.read()
                
                # Write document separator and metadata
                outfile.write("\n" + "=" * 80 + "\n")
                outfile.write(f"DOCUMENT {idx}/{len(txt_files)}: {filename}\n")
                outfile.write(f"Source: {filename}\n")
                outfile.write(f"Characters: {len(content):,}\n")
                outfile.write("=" * 80 + "\n\n")
                
                # Write content
                outfile.write(content)
                outfile.write("\n\n")
                
                total_chars += len(content)
                print(f"[{idx}/{len(txt_files)}] Added: {filename} ({len(content):,} chars)")
                
            except Exception as e:
                print(f"[{idx}/{len(txt_files)}] Error reading {filename}: {e}")
                outfile.write(f"\n[ERROR: Could not read {filename}: {e}]\n\n")
    
    # Print summary
    print("\n" + "=" * 60)
    print("Consolidation Summary:")
    print(f"Documents processed: {len(txt_files)}")
    print(f"Total characters: {total_chars:,}")
    print(f"Output file: {output_path}")
    print(f"File size: {os.path.getsize(output_path):,} bytes")
    print("=" * 60)
    
    return output_path

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Consolidate all processed documents into a single file")
    parser.add_argument("--output", "-o", type=str, default="consolidated_documents.txt",
                       help="Output filename (default: consolidated_documents.txt)")
    
    args = parser.parse_args()
    
    result = consolidate_documents(args.output)
    
    if result:
        print(f"\nConsolidated document created successfully: {result}")
    else:
<<<<<<< HEAD
        print("\nConsolidation failed.")
=======
        print("\nConsolidation failed.")
>>>>>>> 8d5ee6e1c299e7ec4faba52e139b3a328050d9b4
