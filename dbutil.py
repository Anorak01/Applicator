import json
import os
import sqlite3
import pickle

from action import Action, ActionInteraction


class MessageDB():
    @classmethod
    def add_application_msg(cls, msg_id: str, author_id: str, guild_id: str, app_name: str) -> None:
        data = (msg_id, author_id, guild_id, app_name)
        con = sqlite3.connect("applications.db")
        cur = con.cursor()
        cur.execute("INSERT INTO app_msg_db VALUES (?, ?, ?, ?)", data)
        con.commit()

    @classmethod
    def get_application_msg(cls, msg_id: str) -> tuple[str, str, str]:
        con = sqlite3.connect("applications.db")
        cur = con.cursor()
        cur.execute(f"SELECT user_id, guild_id, app_name FROM app_msg_db WHERE msg_id={msg_id}")
        user_id, guild_id, app_name = cur.fetchone()
        return user_id, guild_id, app_name

    @classmethod
    def remove_application_msg(cls, msg_id: str) -> None:
        con = sqlite3.connect("applications.db")
        cur = con.cursor()
        cur.execute(f"DELETE FROM app_msg_db WHERE msg_id={msg_id}")
        con.commit()


class StartButtonDB():
    @classmethod
    def add_start_msg(cls, msg_id: str, app_name: str, guild_id: str) -> None:
        data = (msg_id, app_name, guild_id)
        con = sqlite3.connect("applications.db")
        cur = con.cursor()
        cur.execute("INSERT INTO app_start_db VALUES (?, ?, ?)", data)
        con.commit()

    @classmethod
    def get_start_msg(cls, msg_id: str) -> tuple[str, str]:
        con = sqlite3.connect("applications.db")
        cur = con.cursor()
        cur.execute("SELECT app_name, guild_id FROM app_start_db WHERE msg_id=?", (str(msg_id), ))
        app_name, guild_id = cur.fetchone()
        return app_name, guild_id

    @classmethod
    def remove_start_msg(cls, msg_id: str) -> None:
        con = sqlite3.connect("applications.db")
        cur = con.cursor()
        cur.execute(f"DELETE FROM app_start_db WHERE msg_id={msg_id}")
        con.commit()

class GuildAppDB():
    @classmethod
    def set_editor_role(cls, guild_id: str, role_id: str) -> None:
        con = sqlite3.connect("applications.db")
        cur = con.cursor()
        cur.execute("UPDATE app_guildapp_db SET editor_role_id = (?) WHERE guild_id= (?)", (role_id, guild_id))
        con.commit()

    @classmethod
    def get_editor_role(cls, guild_id: str) -> int:
        con = sqlite3.connect("applications.db")
        cur = con.cursor()
        cur.execute("SELECT editor_role_id FROM app_guildapp_db WHERE guild_id=(?)", (guild_id, ))
        role_id = cur.fetchone()
        if role_id == "" or role_id == None:
            return -1 # no valid role to check
        else: return role_id

    @classmethod
    def set_reviewer_role(cls, guild_id: str, role_id: str) -> None:
        con = sqlite3.connect("applications.db")
        cur = con.cursor()
        cur.execute("UPDATE app_guildapp_db SET reviewer_role_id = (?) WHERE guild_id= (?)", (role_id, guild_id))
        con.commit()

    @classmethod
    def get_reviewer_role(cls, guild_id: str) -> int:
        con = sqlite3.connect("applications.db")
        cur = con.cursor()
        cur.execute("SELECT reviewer_role_id FROM app_guildapp_db WHERE guild_id=(?)", (guild_id, ))
        role_id = cur.fetchone()
        if role_id == "" or role_id == None:
            return -1 # no valid role to check
        else: return role_id

    @classmethod
    def create_guild(cls, guild_id: str, guild_name: str) -> None:
        applications = {}
        application_blob = pickle.dumps(applications)
        data = guild_id, guild_name, application_blob, "", ""
        con = sqlite3.connect("applications.db")
        cur = con.cursor()
        cur.execute("INSERT INTO app_guildapp_db VALUES (?, ?, ?, ?, ?)", data)
        con.commit()

    @classmethod
    def remove_guild(cls, guild_id: str) -> None:
        con = sqlite3.connect("applications.db")
        cur = con.cursor()
        cur.execute("DELETE FROM app_guildapp_db WHERE guild_id=(?)", (guild_id, ))
        con.commit()

    @classmethod
    def get_all_guilds(cls) -> list:
        con = sqlite3.connect("applications.db")
        cur = con.cursor()
        cur.execute("SELECT guild_id FROM app_guildapp_db")
        guilds = cur.fetchall()
        guilds = [guild[0] for guild in guilds]
        return guilds

    @classmethod
    def add_application_entry(cls, guild_id: str, application_name: str) -> str:
        con = sqlite3.connect("applications.db")
        cur = con.cursor()
        cur.execute("SELECT applications_blob FROM app_guildapp_db WHERE guild_id=(?)", (guild_id, ))
        application_blob = cur.fetchone()
        applications = pickle.loads(application_blob[0])
        if application_name not in applications.keys():
            applications[application_name] = {
                "app_id": "",
                "resp_channel": "",
                "questions": [],
                "actions": []
                }
            application_blob2 = pickle.dumps(applications)
            cur.execute("UPDATE app_guildapp_db SET applications_blob = (?) WHERE guild_id= (?)", (application_blob2, guild_id))
            con.commit()
            return "success"
        else:
            return "error on add application entry: application exists"

    @classmethod
    def remove_application_entry(cls, guild_id: str, application_name: str) -> str:
        con = sqlite3.connect("applications.db")
        cur = con.cursor()
        cur.execute("SELECT applications_blob FROM app_guildapp_db WHERE guild_id=(?)", (guild_id, ))
        application_blob = cur.fetchone()
        applications = pickle.loads(application_blob[0])
        if application_name in applications.keys():
            applications.pop(application_name)
            application_blob2 = pickle.dumps(applications)
            cur.execute("UPDATE app_guildapp_db SET applications_blob = (?) WHERE guild_id= (?)", (application_blob2, guild_id))
            con.commit()
            return "success"
        else:
            return "error on remove application entry: application not found"

    @classmethod
    def get_application_entry(cls, guild_id: str, application_name: str):
        con = sqlite3.connect("applications.db")
        cur = con.cursor()
        cur.execute("SELECT applications_blob FROM app_guildapp_db WHERE guild_id=(?)", (guild_id, ))
        application_blob = cur.fetchone()
        applications = pickle.loads(application_blob[0])
        if application_name in applications.keys():
            return applications[application_name]

    @classmethod
    def get_applications(cls, guild_id: str):
        con = sqlite3.connect("applications.db")
        cur = con.cursor()
        cur.execute("SELECT applications_blob FROM app_guildapp_db WHERE guild_id=(?)", (guild_id, ))
        application_blob = cur.fetchone()
        applications = pickle.loads(application_blob[0])
        return list(applications.keys())

    @classmethod
    def set_response_channel(cls, guild_id: str, application_name: str, channel_id: str) -> str:
        con = sqlite3.connect("applications.db")
        cur = con.cursor()
        cur.execute("SELECT applications_blob FROM app_guildapp_db WHERE guild_id=(?)", (guild_id, ))
        application_blob = cur.fetchone()
        applications = pickle.loads(application_blob[0])
        if application_name in applications.keys():
            applications[application_name]["resp_channel"] = channel_id
            application_blob2 = pickle.dumps(applications)
            cur.execute("UPDATE app_guildapp_db SET applications_blob = (?) WHERE guild_id= (?)", (application_blob2, guild_id))
            con.commit()
            return "success"
        else:
            return "error on set response channel: application not found"

    @classmethod
    def get_response_channel(cls, guild_id: str, application_name: str) -> str:
        con = sqlite3.connect("applications.db")
        cur = con.cursor()
        cur.execute("SELECT applications_blob FROM app_guildapp_db WHERE guild_id=(?)", (guild_id, ))
        application_blob = cur.fetchone()
        applications = pickle.loads(application_blob[0])
        if application_name in applications.keys():
            return applications[application_name]["resp_channel"]

    @classmethod
    def add_question(cls, guild_id: str, application_name: str, question: str) -> str:
        con = sqlite3.connect("applications.db")
        cur = con.cursor()
        cur.execute("SELECT applications_blob FROM app_guildapp_db WHERE guild_id=(?)", (guild_id, ))
        application_blob = cur.fetchone()
        applications = pickle.loads(application_blob[0])
        if application_name in applications.keys():
            question_index = int(len(applications[application_name]["questions"]))
            applications[application_name]["questions"].append(question)
            application_blob2 = pickle.dumps(applications)
            cur.execute("UPDATE app_guildapp_db SET applications_blob = (?) WHERE guild_id= (?)", (application_blob2, guild_id))
            con.commit()
            return "success"
        else:
            return "error on add question: application not found"

    @classmethod
    def get_questions(cls, guild_id: str, application_name: str):
        con = sqlite3.connect("applications.db")
        cur = con.cursor()
        cur.execute("SELECT applications_blob FROM app_guildapp_db WHERE guild_id=(?)", (guild_id, ))
        application_blob = cur.fetchone()
        applications = pickle.loads(application_blob[0])
        if application_name in applications.keys():
            questions = applications[application_name]["questions"]
            return questions, len(questions)
        else:
            return "error on get questions: application not found", ""

    @classmethod
    def edit_question(cls, guild_id: str, application_name: str, question_index: int, new_question: str):
        con = sqlite3.connect("applications.db")
        cur = con.cursor()
        cur.execute("SELECT applications_blob FROM app_guildapp_db WHERE guild_id=(?)", (guild_id, ))
        application_blob = cur.fetchone()
        applications = pickle.loads(application_blob[0])
        if application_name in applications.keys():
            questions = applications[application_name]["questions"]
            if question_index <= len(questions):
                questions[question_index-1] = new_question
                applications[application_name]["questions"] = questions
                application_blob2 = pickle.dumps(applications)
                cur.execute("UPDATE app_guildapp_db SET applications_blob = (?) WHERE guild_id= (?)", (application_blob2, guild_id))
                con.commit()
                return "success"
            else:
                return "error on edit question: question index not found"
        else:
            return "error on edit question: application not found"

    @classmethod
    def move_question(cls, guild_id: str, application_name: str, init_que_index: int, fin_que_index: int):
        con = sqlite3.connect("applications.db")
        cur = con.cursor()
        cur.execute("SELECT applications_blob FROM app_guildapp_db WHERE guild_id=(?)", (guild_id, ))
        application_blob = cur.fetchone()
        applications = pickle.loads(application_blob[0])
        if application_name in applications.keys():
            questions = applications[application_name]["questions"]
            if init_que_index <= len(questions) and fin_que_index <= len(questions):
                if init_que_index > fin_que_index:
                    questions.insert(fin_que_index-1, questions[init_que_index-1])
                    questions.pop(init_que_index)
                elif init_que_index < fin_que_index:
                    questions.insert(fin_que_index, questions[init_que_index-1])
                    questions.pop(init_que_index-1)
                else:
                    return "error on move question: init and fin index equal"
                applications[application_name]["questions"] = questions
                application_blob2 = pickle.dumps(applications)
                cur.execute("UPDATE app_guildapp_db SET applications_blob = (?) WHERE guild_id= (?)", (application_blob2, guild_id))
                con.commit()
                return "success"
            else:
                return "error on move question: question index not found"
        else:
            return "error on move question: application not found"

    @classmethod
    def remove_question(cls, guild_id: str, application_name: str, question_index: int):
        con = sqlite3.connect("applications.db")
        cur = con.cursor()
        cur.execute("SELECT applications_blob FROM app_guildapp_db WHERE guild_id=(?)", (guild_id, ))
        application_blob = cur.fetchone()
        applications = pickle.loads(application_blob[0])
        if application_name in applications.keys():
            questions = applications[application_name]["questions"]
            if question_index <= len(questions):
                questions.pop(question_index-1)
                applications[application_name]["questions"] = questions
                application_blob2 = pickle.dumps(applications)
                cur.execute("UPDATE app_guildapp_db SET applications_blob = (?) WHERE guild_id= (?)", (application_blob2, guild_id))
                con.commit()
                return "success"
            else:
                return "error on remove question: question index not found"
        else:
            return "error on remove question: application not found"

    @classmethod
    def add_action(cls, guild_id: str, application_name: str, action: dict) -> str:
        con = sqlite3.connect("applications.db")
        cur = con.cursor()
        cur.execute("SELECT applications_blob FROM app_guildapp_db WHERE guild_id=(?)", (guild_id, ))
        application_blob = cur.fetchone()
        applications = pickle.loads(application_blob[0])
        if application_name in applications.keys():
            applications[application_name]["actions"].append(action)
            application_blob2 = pickle.dumps(applications)
            cur.execute("UPDATE app_guildapp_db SET applications_blob = (?) WHERE guild_id= (?)", (application_blob2, guild_id))
            con.commit()
            return "success"
        else:
            return "error on add action: application not found"

    @classmethod
    def get_actions(cls, guild_id: str, application_name: str, action_type: ActionInteraction):
        con = sqlite3.connect("applications.db")
        cur = con.cursor()
        cur.execute("SELECT applications_blob FROM app_guildapp_db WHERE guild_id=(?)", (guild_id, ))
        application_blob = cur.fetchone()
        applications = pickle.loads(application_blob[0])
        if application_name in applications.keys():
            actions = applications[application_name]["actions"]
            actret = []
            for i in actions:
                if i["result"] == action_type:
                    actret.append(i)
            return actret
        else:
            return "error on get actions: application not found"

    @classmethod
    def remove_action(cls, guild_id: str, application_name: str, action_type: ActionInteraction, action_index: int):
        con = sqlite3.connect("applications.db")
        cur = con.cursor()
        cur.execute("SELECT applications_blob FROM app_guildapp_db WHERE guild_id=(?)", (guild_id, ))
        application_blob = cur.fetchone()
        applications = pickle.loads(application_blob[0])
        if application_name in applications.keys():
            actions = applications[application_name]["actions"]
            actedit = []
            actnoedit = []
            for i in actions:
                if i["result"] == action_type:
                    actedit.append(i)
                else:
                    actnoedit.append(i)

            if action_index <= len(actedit):
                actedit.pop(action_index-1)

                for x in actedit:
                    actnoedit.append(x)

                applications[application_name]["actions"] = actnoedit
                application_blob2 = pickle.dumps(applications)
                cur.execute("UPDATE app_guildapp_db SET applications_blob = (?) WHERE guild_id= (?)", (application_blob2, guild_id))
                con.commit()
                return "success"
            else:
                return "error on remove action: action index not found"
        else:
            return "error on remove action: application not found"
