import os
import sys
import django

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Auto-detect or specify the settings module
# Your project settings folder is 'alumni_sphere.settings'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alumni_sphere.settings')

try:
    django.setup()
except ModuleNotFoundError:
    # Fallback to single folder settings if 'alumni_sphere' is the root
    os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
    django.setup()

from django.contrib.auth.models import User
from core.models import Profile, Connection, Post, Comment, Message

def seed_database():
    print("🚀 Starting AlumniSphere database seed...")

    # Sample Bot Accounts Data
    bots_data = [
        {
            'username': 'alex_dev',
            'first_name': 'Alex',
            'last_name': 'Rivera',
            'email': 'alex.rivera@example.com',
            'role': 'alumni',
            'job_title': 'Senior Full Stack Engineer',
            'company': 'Google',
            'location': 'San Francisco, CA',
            'graduation_year': 2021,
            'bio': 'Passionate about building scalable web applications and mentoring junior developers in Python & React.'
        },
        {
            'username': 'sara_design',
            'first_name': 'Sara',
            'last_name': 'Chen',
            'email': 'sara.chen@example.com',
            'role': 'alumni',
            'job_title': 'Lead Product Designer',
            'company': 'Figma',
            'location': 'New York, NY',
            'graduation_year': 2022,
            'bio': 'Focusing on accessibility, design systems, and seamless SaaS user interfaces.'
        },
        {
            'username': 'marcus_tech',
            'first_name': 'Marcus',
            'last_name': 'Vance',
            'email': 'marcus.v@example.com',
            'role': 'student',
            'job_title': 'CS Undergrad / AI Researcher',
            'company': 'University AI Lab',
            'location': 'Boston, MA',
            'graduation_year': 2027,
            'bio': 'Currently exploring LLM agent architectures, Django backends, and open-source software.'
        },
        {
            'username': 'priya_data',
            'first_name': 'Priya',
            'last_name': 'Sharma',
            'email': 'priya.s@example.com',
            'role': 'alumni',
            'job_title': 'Data Scientist',
            'company': 'Microsoft',
            'location': 'Seattle, WA',
            'graduation_year': 2020,
            'bio': 'Building data pipelines and machine learning models. Always open to mentoring CS students!'
        },
        {
            'username': 'jordan_builds',
            'first_name': 'Jordan',
            'last_name': 'Lee',
            'email': 'jordan.lee@example.com',
            'role': 'student',
            'job_title': 'Software Engineering Intern',
            'company': 'Stripe',
            'location': 'Austin, TX',
            'graduation_year': 2026,
            'bio': 'Building side projects with Django, Bootstrap 5, and SQLite. Big fan of clean code.'
        }
    ]

    created_users = []

    # 1. Create Users and Profiles
    for data in bots_data:
        user, created = User.objects.get_or_create(
            username=data['username'],
            defaults={
                'first_name': data['first_name'],
                'last_name': data['last_name'],
                'email': data['email']
            }
        )
        if created:
            user.set_password('Password123!')
            user.save()

        # Update profile details created by signal
        profile = user.profile
        profile.role = data['role']
        profile.job_title = data['job_title']
        profile.company = data['company']
        profile.location = data['location']
        profile.graduation_year = data['graduation_year']
        profile.bio = data['bio']
        profile.linkedin_url = f"https://linkedin.com/in/{data['username']}"
        profile.github_url = f"https://github.com/{data['username']}"
        profile.save()

        created_users.append(user)
        print(f"✅ Bot account created: @{user.username}")

    # Fetch your logged-in user account (or fallback to the first bot)
    main_user = User.objects.exclude(id__in=[u.id for u in created_users]).first() or created_users[0]

    # 2. Seed Connection Requests
    print("\n🤝 Creating Connection Requests...")
    Connection.objects.get_or_create(sender=created_users[0], receiver=main_user, status='pending')
    Connection.objects.get_or_create(sender=created_users[1], receiver=main_user, status='pending')
    Connection.objects.get_or_create(sender=created_users[2], receiver=created_users[3], status='accepted')

    # 3. Seed Posts & Engagement
    print("\n📝 Creating Feed Posts, Likes, and Comments...")
    post_data_list = [
        (created_users[0], "Just published a new article on optimizing Django QuerySets and database indexing! 🚀 Let me know your thoughts: https://djangoproject.com"),
        (created_users[1], "Working on modern glassmorphic component libraries for our SaaS dashboard. Design systems make scaling so much smoother! 💡👍"),
        (created_users[2], "Excited to share that our team completed the AI Interview Coach demo project today! Built with Django, JavaScript, and custom CSS. 🎉🎓"),
        (created_users[3], "To all students applying for summer engineering internships: keep your GitHub activity consistent and double check your resume formatting! 💻👏"),
    ]

    posts = []
    for author, content in post_data_list:
        post, _ = Post.objects.get_or_create(author=author, content=content)
        posts.append(post)

        # Add likes
        post.likes.add(created_users[1], created_users[2], created_users[3])

    # Add comments
    if posts:
        Comment.objects.get_or_create(post=posts[0], author=created_users[2], defaults={'content': "Great read, Alex! The section on prefetch_related was super helpful."})
        Comment.objects.get_or_create(post=posts[0], author=created_users[3], defaults={'content': "Thanks for sharing! Adding this to my bookmarks."})
        Comment.objects.get_or_create(post=posts[2], author=created_users[0], defaults={'content': "Congrats Marcus! Looking forward to testing the app."})

    # 4. Seed Direct Messages for Notification Bell Testing
    print("\n💬 Creating Direct Messages & Unread Notifications...")
    Message.objects.create(
        sender=created_users[0],
        receiver=main_user,
        content="Hey! I saw your recent updates on AlumniSphere. Great progress on the messaging setup! 👍",
        is_read=False
    )
    Message.objects.create(
        sender=created_users[1],
        receiver=main_user,
        content="Hi there! Do you have a few minutes this week to discuss product design best practices?",
        is_read=False
    )
    Message.objects.create(
        sender=created_users[3],
        receiver=main_user,
        content="Hello! Just reviewing your profile. Let me know if you need any feedback on your CV.",
        is_read=False
    )

    print("\n🎉 Seeding completed successfully!")
    print(f"👉 Default password for all bot accounts: Password123!")
    print(f"👉 Target user for unread notifications: @{main_user.username}")

if __name__ == '__main__':
    seed_database()