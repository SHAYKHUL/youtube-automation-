#!/usr/bin/env python3
"""
Test the Facebook extraction with the actual problematic text from CSV
"""

from email_finder import extract_emails_and_socials

def test_csv_facebook_issue():
    """Test with the actual text that was causing profile.php? issue"""
    
    # This is the actual redirect URL from the CSV that was causing issues
    problematic_text = """redirect?event=video_description&redir_token=quffluhqbxdxdddsne5trtvwsjvyzzjgbl9llvrnewxhuxxbq3jtc0tuxzbuelhyue1wszlsb3mwyk9tzepiu3fsqu9cs19qwfhfou9xt3d6ovrsm1zedwnuvxllszcwqxzjvzhqn1byltjsvddxbjzlb284zmjzwwzjcmq4evlwsgdyejdmuw55mxz4rg1fb1rkanr0r3u1vq&q=https%3a%2f%2fwww.facebook.com%2fprofile.php%3fid%3d100088203832962&v=4vpurs2prnq"""
    
    print("🔍 Testing CSV Facebook Issue")
    print("="*60)
    print("Input text:")
    print(problematic_text)
    print("\n" + "-"*60)
    
    emails, socials, usernames = extract_emails_and_socials(problematic_text)
    
    print("Results:")
    print(f"📧 Emails: {emails}")
    print(f"📱 Social platforms: {list(socials.keys())}")
    
    if 'facebook' in socials:
        print(f"📘 Facebook links: {socials['facebook']}")
        
        for link in socials['facebook']:
            if 'profile.php?id=100088203832962' in link:
                print("✅ SUCCESS: Complete Facebook profile URL found!")
                print(f"   Full URL: {link}")
            else:
                print("❌ Issue: Facebook URL incomplete")
                print(f"   Found: {link}")
    else:
        print("❌ No Facebook links found")
    
    print(f"👤 Usernames: {usernames}")

if __name__ == "__main__":
    test_csv_facebook_issue()
    print("\n✅ CSV Facebook issue test completed!")
