import json
import os
import pickle
import sqlite3
from typing import Any

from action import Action, ActionInteraction

_con = sqlite3.connect("applications.db")
_con.execute("PRAGMA journal_mode=WAL")


class MessageDB:
    @classmethod
    def add_application_msg(
        cls, msg_id: str, author_id: str, guild_id: str, app_name: str
    ) -> None:
        data = (msg_id, author_id, guild_id, app_name)
        cur = _con.cursor()
        cur.execute("INSERT INTO app_msg_db VALUES (?, ?, ?, ?)", data)
        _con.commit()

    @classmethod
    def get_application_msg(cls, msg_id: str) -> tuple[str, str, str]:
        cur = _con.cursor()
        cur.execute(
            "SELECT user_id, guild_id, app_name FROM app_msg_db WHERE msg_id=?",
            (msg_id,),
        )
        return cur.fetchone()

    @classmethod
    def remove_application_msg(cls, msg_id: str) -> None:
        cur = _con.cursor()
        cur.execute("DELETE FROM app_msg_db WHERE msg_id=?", (msg_id,))
        _con.commit()


class StartButtonDB:
    @classmethod
    def add_start_msg(cls, msg_id: str, app_name: str, guild_id: str) -> None:
        data = (msg_id, app_name, guild_id)
        cur = _con.cursor()
        cur.execute("INSERT INTO app_start_db VALUES (?, ?, ?)", data)
        _con.commit()

    @classmethod
    def get_start_msg(cls, msg_id: str) -> tuple[str, str]:
        cur = _con.cursor()
        cur.execute(
            "SELECT app_name, guild_id FROM app_start_db WHERE msg_id=?", (str(msg_id),)
        )
        return cur.fetchone()

    @classmethod
    def remove_start_msg(cls, msg_id: str) -> None:
        cur = _con.cursor()
        cur.execute("DELETE FROM app_start_db WHERE msg_id=?", (msg_id,))
        _con.commit()


class GuildAppDB:
    @classmethod
    def set_editor_role(cls, guild_id: str, role_id: str) -> None:
        cur = _con.cursor()
        cur.execute(
            "UPDATE app_guildapp_db SET editor_role_id = (?) WHERE guild_id= (?)",
            (role_id, guild_id),
        )
        _con.commit()

    @classmethod
    def get_editor_role(cls, guild_id: str) -> int:
        cur = _con.cursor()
        cur.execute(
            "SELECT editor_role_id FROM app_guildapp_db WHERE guild_id=(?)", (guild_id,)
        )
        role_id = cur.fetchone()
        if role_id[0] == "" or role_id[0] == None:
            return -1  # no valid role to check
        else:
            return int(role_id[0])

    @classmethod
    def set_reviewer_role(cls, guild_id: str, role_id: str) -> None:
        cur = _con.cursor()
        cur.execute(
            "UPDATE app_guildapp_db SET reviewer_role_id = (?) WHERE guild_id= (?)",
            (role_id, guild_id),
        )
        _con.commit()

    @classmethod
    def get_reviewer_role(cls, guild_id: str) -> int:
        cur = _con.cursor()
        cur.execute(
            "SELECT reviewer_role_id FROM app_guildapp_db WHERE guild_id=(?)",
            (guild_id,),
        )
        role_id = cur.fetchone()
        if role_id[0] == "" or role_id[0] == None:
            return -1  # no valid role to check
        else:
            return int(role_id[0])

    @classmethod
    def create_guild(cls, guild_id: str, guild_name: str) -> None:
        applications = {}
        application_blob = pickle.dumps(applications)
        data = guild_id, guild_name, application_blob, "", ""
        cur = _con.cursor()
        cur.execute("INSERT INTO app_guildapp_db VALUES (?, ?, ?, ?, ?)", data)
        _con.commit()

    @classmethod
    def remove_guild(cls, guild_id: str) -> None:
        cur = _con.cursor()
        cur.execute("DELETE FROM app_guildapp_db WHERE guild_id=(?)", (guild_id,))
        _con.commit()

    @classmethod
    def get_all_guilds(cls) -> list:
        cur = _con.cursor()
        cur.execute("SELECT guild_id FROM app_guildapp_db")
        guilds = cur.fetchall()
        return [guild[0] for guild in guilds]

    @classmethod
    def add_application_entry(cls, guild_id: str, application_name: str) -> str:
        cur = _con.cursor()
        cur.execute("BEGIN IMMEDIATE")
        cur.execute(
            "SELECT applications_blob FROM app_guildapp_db WHERE guild_id=(?)",
            (guild_id,),
        )
        applications = pickle.loads(cur.fetchone()[0])
        if application_name not in applications.keys():
            applications[application_name] = {
                "app_id": "",
                "resp_channel": "",
                "questions": [],
                "actions": [],
            }
            cur.execute(
                "UPDATE app_guildapp_db SET applications_blob = (?) WHERE guild_id= (?)",
                (pickle.dumps(applications), guild_id),
            )
            _con.commit()
            return "success"
        else:
            return "error on add application entry: application exists"

    @classmethod
    def remove_application_entry(cls, guild_id: str, application_name: str) -> str:
        cur = _con.cursor()
        cur.execute("BEGIN IMMEDIATE")
        cur.execute(
            "SELECT applications_blob FROM app_guildapp_db WHERE guild_id=(?)",
            (guild_id,),
        )
        applications = pickle.loads(cur.fetchone()[0])
        if application_name in applications.keys():
            applications.pop(application_name)
            cur.execute(
                "UPDATE app_guildapp_db SET applications_blob = (?) WHERE guild_id= (?)",
                (pickle.dumps(applications), guild_id),
            )
            _con.commit()
            return "success"
        else:
            return "error on remove application entry: application not found"

    @classmethod
    def get_application_entry(cls, guild_id: str, application_name: str):
        cur = _con.cursor()
        cur.execute(
            "SELECT applications_blob FROM app_guildapp_db WHERE guild_id=(?)",
            (guild_id,),
        )
        applications = pickle.loads(cur.fetchone()[0])
        if application_name in applications.keys():
            return applications[application_name]

    @classmethod
    def get_applications(cls, guild_id: str):
        cur = _con.cursor()
        cur.execute(
            "SELECT applications_blob FROM app_guildapp_db WHERE guild_id=(?)",
            (guild_id,),
        )
        applications = pickle.loads(cur.fetchone()[0])
        return list(applications.keys())

    @classmethod
    def set_response_channel(
        cls, guild_id: str, application_name: str, channel_id: str
    ) -> str:
        cur = _con.cursor()
        cur.execute("BEGIN IMMEDIATE")
        cur.execute(
            "SELECT applications_blob FROM app_guildapp_db WHERE guild_id=(?)",
            (guild_id,),
        )
        applications = pickle.loads(cur.fetchone()[0])
        if application_name in applications.keys():
            applications[application_name]["resp_channel"] = channel_id
            cur.execute(
                "UPDATE app_guildapp_db SET applications_blob = (?) WHERE guild_id= (?)",
                (pickle.dumps(applications), guild_id),
            )
            _con.commit()
            return "success"
        else:
            return "error on set response channel: application not found"

    @classmethod
    def get_response_channel(cls, guild_id: str, application_name: str) -> str | None:
        cur = _con.cursor()
        cur.execute(
            "SELECT applications_blob FROM app_guildapp_db WHERE guild_id=(?)",
            (guild_id,),
        )
        applications = pickle.loads(cur.fetchone()[0])
        if application_name in applications.keys():
            return applications[application_name]["resp_channel"]

    @classmethod
    def add_question(cls, guild_id: str, application_name: str, question: str) -> str:
        cur = _con.cursor()
        cur.execute("BEGIN IMMEDIATE")
        cur.execute(
            "SELECT applications_blob FROM app_guildapp_db WHERE guild_id=(?)",
            (guild_id,),
        )
        applications = pickle.loads(cur.fetchone()[0])
        if application_name in applications.keys():
            applications[application_name]["questions"].append(question)
            cur.execute(
                "UPDATE app_guildapp_db SET applications_blob = (?) WHERE guild_id= (?)",
                (pickle.dumps(applications), guild_id),
            )
            _con.commit()
            return "success"
        else:
            return "error on add question: application not found"

    @classmethod
    def get_questions(cls, guild_id: str, application_name: str):
        cur = _con.cursor()
        cur.execute(
            "SELECT applications_blob FROM app_guildapp_db WHERE guild_id=(?)",
            (guild_id,),
        )
        applications = pickle.loads(cur.fetchone()[0])
        if application_name in applications.keys():
            questions = applications[application_name]["questions"]
            return questions, len(questions)
        else:
            return "error on get questions: application not found", ""

    @classmethod
    def edit_question(
        cls,
        guild_id: str,
        application_name: str,
        question_index: int,
        new_question: str,
    ):
        cur = _con.cursor()
        cur.execute("BEGIN IMMEDIATE")
        cur.execute(
            "SELECT applications_blob FROM app_guildapp_db WHERE guild_id=(?)",
            (guild_id,),
        )
        applications = pickle.loads(cur.fetchone()[0])
        if application_name in applications.keys():
            questions = applications[application_name]["questions"]
            if question_index <= len(questions):
                questions[question_index - 1] = new_question
                applications[application_name]["questions"] = questions
                cur.execute(
                    "UPDATE app_guildapp_db SET applications_blob = (?) WHERE guild_id= (?)",
                    (pickle.dumps(applications), guild_id),
                )
                _con.commit()
                return "success"
            else:
                return "error on edit question: question index not found"
        else:
            return "error on edit question: application not found"

    @classmethod
    def move_question(
        cls,
        guild_id: str,
        application_name: str,
        init_que_index: int,
        fin_que_index: int,
    ):
        cur = _con.cursor()
        cur.execute("BEGIN IMMEDIATE")
        cur.execute(
            "SELECT applications_blob FROM app_guildapp_db WHERE guild_id=(?)",
            (guild_id,),
        )
        applications = pickle.loads(cur.fetchone()[0])
        if application_name in applications.keys():
            questions = applications[application_name]["questions"]
            if init_que_index <= len(questions) and fin_que_index <= len(questions):
                if init_que_index > fin_que_index:
                    questions.insert(fin_que_index - 1, questions[init_que_index - 1])
                    questions.pop(init_que_index)
                elif init_que_index < fin_que_index:
                    questions.insert(fin_que_index, questions[init_que_index - 1])
                    questions.pop(init_que_index - 1)
                else:
                    return "error on move question: init and fin index equal"
                applications[application_name]["questions"] = questions
                cur.execute(
                    "UPDATE app_guildapp_db SET applications_blob = (?) WHERE guild_id= (?)",
                    (pickle.dumps(applications), guild_id),
                )
                _con.commit()
                return "success"
            else:
                return "error on move question: question index not found"
        else:
            return "error on move question: application not found"

    @classmethod
    def remove_question(cls, guild_id: str, application_name: str, question_index: int):
        cur = _con.cursor()
        cur.execute("BEGIN IMMEDIATE")
        cur.execute(
            "SELECT applications_blob FROM app_guildapp_db WHERE guild_id=(?)",
            (guild_id,),
        )
        applications = pickle.loads(cur.fetchone()[0])
        if application_name in applications.keys():
            questions = applications[application_name]["questions"]
            if question_index <= len(questions):
                questions.pop(question_index - 1)
                applications[application_name]["questions"] = questions
                cur.execute(
                    "UPDATE app_guildapp_db SET applications_blob = (?) WHERE guild_id= (?)",
                    (pickle.dumps(applications), guild_id),
                )
                _con.commit()
                return "success"
            else:
                return "error on remove question: question index not found"
        else:
            return "error on remove question: application not found"

    @classmethod
    def add_action(cls, guild_id: str, application_name: str, action: dict) -> str:
        cur = _con.cursor()
        cur.execute("BEGIN IMMEDIATE")
        cur.execute(
            "SELECT applications_blob FROM app_guildapp_db WHERE guild_id=(?)",
            (guild_id,),
        )
        applications = pickle.loads(cur.fetchone()[0])
        if application_name in applications.keys():
            applications[application_name]["actions"].append(action)
            cur.execute(
                "UPDATE app_guildapp_db SET applications_blob = (?) WHERE guild_id= (?)",
                (pickle.dumps(applications), guild_id),
            )
            _con.commit()
            return "success"
        else:
            return "error on add action: application not found"

    @classmethod
    def get_actions(
        cls, guild_id: str, application_name: str, action_type: ActionInteraction
    ) -> list[dict[str, Any]] | str:
        cur = _con.cursor()
        cur.execute(
            "SELECT applications_blob FROM app_guildapp_db WHERE guild_id=(?)",
            (guild_id,),
        )
        applications = pickle.loads(cur.fetchone()[0])
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
    def remove_action(
        cls,
        guild_id: str,
        application_name: str,
        action_type: ActionInteraction,
        action_index: int,
    ):
        cur = _con.cursor()
        cur.execute("BEGIN IMMEDIATE")
        cur.execute(
            "SELECT applications_blob FROM app_guildapp_db WHERE guild_id=(?)",
            (guild_id,),
        )
        applications = pickle.loads(cur.fetchone()[0])
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
                actedit.pop(action_index - 1)
                for x in actedit:
                    actnoedit.append(x)

                applications[application_name]["actions"] = actnoedit
                cur.execute(
                    "UPDATE app_guildapp_db SET applications_blob = (?) WHERE guild_id= (?)",
                    (pickle.dumps(applications), guild_id),
                )
                _con.commit()
                return "success"
            else:
                return "error on remove action: action index not found"
        else:
            return "error on remove action: application not found"
