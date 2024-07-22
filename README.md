# Applicator

My own discord bot for applications. Not only staff, you can make anything! Every application and it's actions are editable using in-discord GUI! So no more annoying websites.

**Now finally with basic permissions!**

---

Support me on [Ko-fi](https://ko-fi.com/anorak01)

[Invite](https://discord.com/api/oauth2/authorize?client_id=1143622923136024767&permissions=1119107533846&scope=bot%20applications.commands) Applicator public instance to your server

---
### Why?

You know the feeling when you just want a simple application for your discord server and whatever you find has only website editor and features blocked under subscription?

Yeah... me too
So I made this

---

### Features

- Database driven multi-guild bot ✔️
- Easy to use in-discord editor for applications ✔️
- Start the application with a push of a button ✔️
- Application Actions™✔️*add custom roles, send messages to channels based on contents of the application*
- Paid tier ❌

### Plans

- Rework the code and redesign Actions™ backend
- Better permission management - application operations requires Administrator permissions for now
- More ways to go through the application process - modals, interview channel
- Add new Actions™ - remove role, send message to channel, etc. - ideas welcome

---

### Usage

The bot is based on `/slash` commands, so you can just type `/` in Discord and check out the commands

- `/start_button` - creates a Start button for your application
- `/application create [name]` - creates an application
- `/application remove [name]` - removes an application
- `/application list` - lists all applications
- `/application response_channel` - set channel where all finished applications get sent
- `/application editor` - opens editor for selected application
- `/application actions` - opens editor for Actions™ of application
- `/application set_editor_role` - sets the editor role, this enables access to working with applications on your server
- `/application set_reviewer_role` - sets the reviewer role, this enables access to accepting and declining applications from users

---
### Installation

1. Clone repo `git clone https://github.com/Anorak01/Applicator`
2. Rename `.env.example` to `.env` and paste in your bot token  [How to get bot token](https://docs.pycord.dev/en/stable/discord.html)
3. Install dependencies `pip install -r requirements.txt`
4. Initialize database `python3 setup.py`
5. Start the bot `python3 bot.py`
6. Enjoy!

---

### Author notes

Yes it's messy, yes I'm working on it.
No, I don't care about pushing to main on a single person project.