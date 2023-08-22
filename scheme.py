#applications.db -> app_guildapp_db -> applications_blob
from action import Action, ActionInteraction

application_name: {
    "app_id": "", # basically useless but hey its there
    "resp_channel": "",
    "questions": [],
    "actions": {
        "action_name": Action(ActionInteraction.ACCEPT).add_role(),
        "action_name2": Action(ActionInteraction.DECLINE),

    }
}

application_name: {
    "app_id": "", # basically useless but hey its there
    "resp_channel": "",
    "questions": [],
    "actions": [
            {
            "result": ActionInteraction.ACCEPT,
            "action_type": "action_type",
            "data": ""
            },
        {}

    ]
}

