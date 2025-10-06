import csv

# Test reading the save.csv file
print("🔍 Testing save.csv reading...")
channel_links = []

try:
    with open('save.csv', 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        row_count = 0
        for row in reader:
            row_count += 1
            if row_count <= 5:  # Show first 5 rows
                print(f"Row {row_count}: {row}")
            
            if row and row[0].startswith('http'):
                channel_links.append(row[0])
        
        print(f"\n📊 Total rows in CSV: {row_count}")
        print(f"📊 Valid channel links found: {len(channel_links)}")
        
        if len(channel_links) > 0:
            print(f"📊 First few channel links:")
            for i, link in enumerate(channel_links[:5]):
                print(f"  {i+1}. {link}")
        else:
            print("❌ No valid channel links found!")
            
except Exception as e:
    print(f"❌ Error reading save.csv: {e}")
