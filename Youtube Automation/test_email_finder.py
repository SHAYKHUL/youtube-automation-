import csv
from email_finder import extract_emails_and_socials

def test_extraction():
    """Test the email and social media extraction functionality"""
    print("🧪 Testing Email & Social Media Extraction")
    print("=" * 50)
    
    test_cases = [
        {
            'name': 'Email + Social Mix',
            'text': 'Contact me at john@example.com or follow @johndoe on Instagram: instagram.com/johndoe, Facebook: facebook.com/john.doe'
        },
        {
            'name': 'Only Social Media',
            'text': 'Follow me on TikTok @coolcreator and Twitter twitter.com/coolcreator, website: www.mycoolsite.com'
        },
        {
            'name': 'Multiple Emails',
            'text': 'Business: business@company.com Personal: personal@gmail.com'
        },
        {
            'name': 'Complex Social',
            'text': 'Find me on IG: @photographer_pro, FB: facebook.com/photographer.pro, X: x.com/photopro, website: https://photopro.com'
        },
        {
            'name': 'No Contact Info',
            'text': 'This is just a regular description about my channel with no contact information at all.'
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n🔍 Test {i}: {test['name']}")
        print(f"📝 Text: {test['text'][:80]}...")
        
        emails, socials, usernames = extract_emails_and_socials(test['text'])
        
        print(f"📧 Emails: {emails}")
        print(f"📱 Social: {socials}")
        print(f"👤 Usernames: {usernames}")
        print("-" * 40)

def check_csv_files():
    """Check if CSV files exist and show their structure"""
    print("\n📁 Checking CSV Files")
    print("=" * 30)
    
    files_to_check = [
        'founded_email.csv',
        'not_email_but_social.csv', 
        'non_founded_email.csv',
        'signin_to_see_email.csv'
    ]
    
    for filename in files_to_check:
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                rows = list(reader)
                print(f"✅ {filename}: {len(rows)} rows")
                if rows:
                    print(f"   Headers: {rows[0]}")
                    if len(rows) > 1:
                        print(f"   Sample: {rows[1][0] if len(rows[1]) > 0 else 'Empty'}")
        except FileNotFoundError:
            print(f"❌ {filename}: File not found")
        except Exception as e:
            print(f"❌ {filename}: Error reading file - {e}")

def create_test_csv():
    """Create a small test CSV file"""
    test_channels = [
        "https://www.youtube.com/@examplechannel1",
        "https://www.youtube.com/@examplechannel2",
        "https://www.youtube.com/@examplechannel3"
    ]
    
    with open('test_channels.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Channel Link'])
        for channel in test_channels:
            writer.writerow([channel])
    
    print("✅ Created test_channels.csv with 3 sample channels")

def main():
    print("🧪 Email Finder Test Suite")
    print("=" * 40)
    
    choice = input("Choose test:\n1. Test text extraction\n2. Check CSV files\n3. Create test CSV\n4. All tests\nEnter choice (1-4): ")
    
    if choice in ['1', '4']:
        test_extraction()
    
    if choice in ['2', '4']:
        check_csv_files()
    
    if choice in ['3', '4']:
        create_test_csv()
    
    print("\n✅ Testing complete!")

if __name__ == "__main__":
    main()
