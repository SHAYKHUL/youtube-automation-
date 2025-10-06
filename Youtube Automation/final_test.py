import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from email_finder import extract_emails_and_socials

def test_final_extraction():
    print("🎯 Final Comprehensive Test")
    print("=" * 60)
    
    # Test 1: Facebook profile.php URL
    test_facebook = """
    redirect?event=video_description&redir_token=quffluhqbxdxdddsne5trtvwsjvyzzjgbl9llvrnewxhuxxbq3jtc0tuxzbuelhyu
    e1wszlsb3mwyk9tzepiu3fsqu9cs19qwfhfou9xt3d6ovrsm1zedwnuvxllszcwqxzjvzhqn1byltjsvddxbjzlb284zmjzwwzjcmq4evlwsgdyejdmuw55mxz4rg1fb1rkanr0r3u1vq&q=https%3a%2f%2fwww.facebook.com%2fprofile.php%3fid%3d100088203832962&v=4vpurs2prnq
    """
    
    # Test 2: Mixed social media
    test_mixed = """
    Follow us on:
    Instagram: @mychannel
    Twitter: https://twitter.com/user123
    Facebook: https://www.facebook.com/mypage
    Email: contact@example.com
    """
    
    # Test 3: Sign in to see email
    test_signin = """
    <div class="about-description">
        <p>For business inquiries:</p>
        <p>Sign in to see email address</p>
        <p>Follow us on Instagram @mychannel</p>
    </div>
    """
    
    print("🧪 Test 1: Facebook profile.php URL")
    emails1, socials1, usernames1 = extract_emails_and_socials(test_facebook)
    print(f"📧 Emails: {emails1}")
    print(f"📱 Social platforms: {list(socials1.keys())}")
    print(f"📘 Facebook: {socials1.get('facebook', [])}")
    print(f"� Usernames: {usernames1}")
    
    print("\n🧪 Test 2: Mixed social media")
    emails2, socials2, usernames2 = extract_emails_and_socials(test_mixed)
    print(f"📧 Emails: {emails2}")
    print(f"📱 Social platforms: {list(socials2.keys())}")
    print(f"📘 Facebook: {socials2.get('facebook', [])}")
    print(f"🐦 Twitter: {socials2.get('twitter', [])}")
    print(f"📸 Instagram: {socials2.get('instagram', [])}")
    print(f"👤 Usernames: {usernames2}")
    
    print("\n🧪 Test 3: Sign in to see email (checking signin detection)")
    # For signin detection, we need the full contact finder function
    from email_finder import get_contact_info_from_youtube_channel
    print("� This would require full channel URL for signin detection test")
    
    print("\n✅ Final test completed!")

if __name__ == "__main__":
    test_final_extraction()
