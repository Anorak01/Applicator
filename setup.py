import sqlite3

con = sqlite3.connect("applications.db")
cur = con.cursor()
cur.execute("CREATE TABLE app_msg_db(msg_id, user_id, guild_id, app_name)")
cur.execute("CREATE TABLE app_guildapp_db(guild_id, guild_name, applications_blob, editor_role_id, reviewer_role_id)")
cur.execute("CREATE TABLE app_start_db(msg_id, app_name, guild_id)")
con.commit()
