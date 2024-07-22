# db - msg_id, user_id, guild_id

import asyncio
import discord
import os
import json
import pickle
import time
import datetime
from dotenv import load_dotenv
from discord.ui import Modal, InputText
from discord.utils import get
from discord.ext import commands
from dbutil import MessageDB
from dbutil import StartButtonDB
from dbutil import GuildAppDB

from action import Action, ActionInteraction, actions

usable_actions = actions

#global owner_icon_url

load_dotenv()

TOKEN = os.getenv("TOKEN")
INVITE_LINK = os.getenv("INVITE_LINK")
SUPPORT_LINK = os.getenv("SUPPORT_LINK")
bot = discord.Bot(intents=discord.Intents.default())


@bot.event
async def on_ready():
    bot.add_view(ApplicationButtonsView())
    bot.add_view(ApplicationStartButtonView())
    activity = discord.Activity(name=f"{len(bot.guilds)} guilds", type=discord.ActivityType.listening)
    await bot.change_presence(activity=activity, status = discord.Status.online)
    app_info = await bot.application_info()

    global owner_icon_url  # I don't like this either, trust me
    owner_icon_url = app_info.owner.avatar.url

    print("Started guild sync")
    new_guild_count = 0
    for i in bot.guilds:
        if str(i.id) not in GuildAppDB.get_all_guilds():
            GuildAppDB.create_guild(str(i.id), i.name)
            new_guild_count+=1
            print(f"Entry for {i.id} created")

    print(f"Logged in as {bot.user}")

    await bot.sync_commands(force=True)
    print("Command sync finished")

@bot.event
async def on_guild_join(guild):
    activity = discord.Activity(name=f"{len(bot.guilds)} guilds", type=discord.ActivityType.listening)
    await bot.change_presence(activity=activity, status = discord.Status.online)
    GuildAppDB.create_guild(str(guild.id), guild.name)
    print(f"Joined guild {guild.name}: {guild.id}")

@bot.event
async def on_guild_remove(guild):
    activity = discord.Activity(name=f"{len(bot.guilds)} guilds", type=discord.ActivityType.listening)
    await bot.change_presence(activity=activity, status = discord.Status.online)
    print(f"Removed from guild {guild.name}: {guild.id}")

@bot.event
async def on_application_command_error(ctx: discord.ApplicationContext, error: discord.DiscordException):
    if isinstance(error, commands.MissingPermissions):
        await ctx.respond("You need Administrator permissions to use this command", ephemeral=True)
        print(f"{ctx.guild.name} {ctx.user.display_name} needs admin")
    else:
        raise error  # Error go brrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr

def is_editor_or_admin():
    async def predicate(ctx):
        editor_role_id = GuildAppDB.get_editor_role(str(ctx.guild.id))
        user_role = ctx.user.get_role(editor_role_id)
        if ctx.user.guild_permissions.administrator: return True
        elif user_role != None: return True
        else: return False

    return commands.check(predicate)

def is_reviewer_or_admin():
    async def predicate(ctx):
        reviewer_role_id = GuildAppDB.get_reviewer_role(str(ctx.guild.id))
        user_role = ctx.user.get_role(reviewer_role_id)
        if ctx.user.guild_permissions.administrator: return True
        elif user_role != None: return True
        else: return False

    return commands.check(predicate)

def is_reviewer_or_admin_func(ctx: discord.Interaction):
    reviewer_role_id = GuildAppDB.get_reviewer_role(str(ctx.guild.id))
    user_role = ctx.user.get_role(reviewer_role_id)
    if ctx.user.guild_permissions.administrator: return True
    elif user_role != None: return True
    else: return False

@bot.slash_command(description = "A help command to get you started")
async def help(ctx):
    embed = discord.Embed(title="Applicator Help", description="Applicator is an open-source Discord application bot that's easy to setup directly in Discord. \nEvery command is usable with /slash. \nWith the new permission system, you need editor or reviewer role to work with the bot.\nBeing Administrator overrides this requirement.")
    embed.add_field(name="```/application create [name]```", value="Creates a new application", inline=False)
    embed.add_field(name="```/application response_channel```", value="Sets the response channel for application. **Important**", inline=False)
    embed.add_field(name="```/application remove [name]```", value="Removes specified application", inline=False)
    embed.add_field(name="```/application list```", value="Lists all applications", inline=False)
    embed.add_field(name="```/application editor```", value="Opens editor for application", inline=False)
    embed.add_field(name="```/application actions```", value="Opens action editor for application", inline=False)
    embed.add_field(name="```/application set_editor_role```", value="Sets editor role. Users with this role can create, edit and remove applications and actions", inline=False)
    embed.add_field(name="```/application set_reviewer_role```", value="Sets reviewer role. Users with this role can review applications", inline=False)
    embed.add_field(name="```/start_button```", value="Creates start button for specified application", inline=False)
    await ctx.response.send_message(embed=embed, ephemeral=True)

@bot.slash_command(description = "Command used to set up the application prompt")
@is_editor_or_admin()
async def start_button(ctx):
    view = discord.ui.View()
    options = SelectApplicationStartButton(max_values=1, placeholder="Select application")
    applications = GuildAppDB.get_applications(str(ctx.guild.id))
    if len(applications) == 0:
        await ctx.response.send_message(content="There are no applications setup for the server. \nPlease create an application first.", ephemeral=True)
        return
    for i in applications:
        options.add_option(label=i, value=i)
    view.add_item(options)
    await ctx.response.send_message(view=view, ephemeral=True)

@start_button.error
async def on_application_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.respond("You need Administrator permissions or reviewer role to use this command", ephemeral=True)
    else:
        raise error


@bot.command(description="Posts invite button for the bot")
async def invite(ctx):
    view = discord.ui.View()
    invite_button = discord.ui.Button(label="Invite", style=discord.ButtonStyle.link, url=INVITE_LINK)
    view.add_item(invite_button)
    embed = discord.Embed(title="Invite Me", color=0x70ff50, description="If you like the bot and want to invite it to other servers, click the button below")
    embed.set_footer(text="Made by @anorak01", icon_url=owner_icon_url)
    try:
        await ctx.response.send_message(embed=embed, view=view)
    except discord.HTTPException as e:
        await ctx.response.send_message(content="It looks like the bot owner didn't set up this link correctly")
        raise e

@bot.command(description="Posts support button for the bot")
async def support(ctx):
    view = discord.ui.View()
    invite_button = discord.ui.Button(label="Support server", style=discord.ButtonStyle.link, url=SUPPORT_LINK)
    view.add_item(invite_button)
    embed = discord.Embed(title="Support", color=0x70ff50, description="If you're having issues with the bot, you can join my support server with the button below")
    embed.set_footer(text="Made by @anorak01", icon_url=owner_icon_url)
    try:
        await ctx.response.send_message(embed=embed, view=view)
    except discord.HTTPException as e:
        await ctx.response.send_message(content="It looks like the bot owner didn't set up this link correctly")
        raise e

@bot.command(description="Leave a review", id="review", name="review")
async def review(ctx):
    view = discord.ui.View()
    invite_button = discord.ui.Button(label="Review", style=discord.ButtonStyle.link, url="https://top.gg/bot/1143622923136024767#reviews")
    view.add_item(invite_button)
    embed = discord.Embed(title="Review", color=0x70ff50, description="If you like the bot, please consider leaving a review and upvote my bot, it will really help a lot!")
    embed.set_footer(text="Made by @anorak01", icon_url=owner_icon_url)
    await ctx.response.send_message(embed=embed, view=view)

application = discord.SlashCommandGroup("application", "The main command to manage applications")

@application.command(description="Create application")
@is_editor_or_admin()
async def create(ctx, application):
    if len(application) < 40:
        result = GuildAppDB.add_application_entry(str(ctx.guild.id), application)
        if result == "success":
            view = discord.ui.View()
            options = SelectResponseChannel(select_type=discord.ComponentType.channel_select, channel_types=[discord.ChannelType.text], max_values=1, placeholder="Select channel")
            options.set_app_name(application)
            view.add_item(options)
            await ctx.response.send_message(f"Successfully created application: {application}\n\nPlease set a response channel:", ephemeral=True, view=view) # create a new application, modal with name ask
        else:
            await ctx.response.send_message(f"Application {application} already exists", ephemeral=True)
    else:
        await ctx.response.send_message(f"please choose a different name", ephemeral=True)

@application.command(description="Remove application")
@is_editor_or_admin()
async def remove(ctx, application):
    result = GuildAppDB.remove_application_entry(str(ctx.guild.id), application)
    if result == "success":
        await ctx.response.send_message(f"Successfully removed application: {application}", ephemeral=True)
    else:
        await ctx.response.send_message(f"Application {application} not found", ephemeral=True)

@application.command(description="List all applications")
@is_editor_or_admin()
async def list(ctx):
    applications = GuildAppDB.get_applications(str(ctx.guild.id))
    embed = discord.Embed(title="**List of applications**")
    embed.set_footer(text="Made by @anorak01", icon_url=owner_icon_url)
    if len(applications) == 0:
        embed.title="You haven't created any applications yet."
        embed.description="Create one using the `/application create` command"
    else:
        for i, app in enumerate(applications):
            embed.add_field(value=f"**{i+1}. {app}**", name="", inline=False)
    await ctx.response.send_message(embed=embed, ephemeral=True)

@application.command(description="Opens editor for selected application")
@is_editor_or_admin()
async def editor(ctx: discord.ApplicationContext):
    view = discord.ui.View()
    options = SelectApplicationOptionsEditor(max_values=1, placeholder="Select application")
    applications = GuildAppDB.get_applications(str(ctx.guild.id))
    if applications:
        for i in applications:
            options.add_option(label=i, value=i)
        view.add_item(options)
        await ctx.response.send_message(view=view, ephemeral=True)
    else:
        emb = discord.Embed(title="You haven't created any applications yet.", description="Create one using the `/application create` command")
        emb.set_footer(text="Made by @anorak01", icon_url=owner_icon_url)
        await ctx.response.send_message(embed=emb , ephemeral= True)

@application.command(description="Opens Actions™ editor")
@is_editor_or_admin()
async def actions(ctx):
    view = discord.ui.View()
    options = SelectActionOptionsEditor(max_values=1, placeholder="Select application")
    application  = GuildAppDB.get_applications(str(ctx.guild.id))
    if application:
        for i in GuildAppDB.get_applications(str(ctx.guild.id)):
            options.add_option(label=i, value=i)
        view.add_item(options)
        await ctx.response.send_message(view=view, ephemeral=True)
    else:
        emb = discord.Embed(title="You haven't created any applications yet.", description="Create one using the `/application create` command")
        emb.set_footer(text="Made by @anorak01", icon_url=owner_icon_url)
        await ctx.response.send_message(embed=emb , ephemeral= True)

@application.command(description="Select response channel for application")
@is_editor_or_admin()
async def response_channel(ctx):
    view = discord.ui.View()
    options = SelectApplicationOptionsRespChannel(max_values=1, placeholder="Select application")
    applications = GuildAppDB.get_applications(str(ctx.guild.id))
    if applications:
        for i in GuildAppDB.get_applications(str(ctx.guild.id)):
            options.add_option(label=i, value=i)
        view.add_item(options)
        await ctx.response.send_message(view=view, ephemeral=True)
    else:
        emb = discord.Embed(title="You haven't created any applications yet.", description="Create one using the `/application create` command")
        emb.set_footer(text="Made by @anorak01", icon_url=owner_icon_url)
        await ctx.response.send_message(embed=emb , ephemeral= True)

@application.command()
async def set_editor_role(ctx):
    view = SelectEditorRoleView()
    await ctx.response.send_message(view=view, ephemeral=True)

@application.command()
async def set_reviewer_role(ctx):
    view = SelectReviewerRoleView()
    await ctx.response.send_message(view=view, ephemeral=True)

bot.add_application_command(application) # add application group commands


def get_questions_embed(guild_id, application) -> discord.Embed:
    embed = discord.Embed(title=f"Application: {application}")
    questions, length = GuildAppDB.get_questions(str(guild_id), application)
    for i, que in enumerate(questions):
        embed.add_field(value=f"**{i+1}. {que}**", name="", inline=False)
    embed.set_footer(text="Made by @anorak01", icon_url=owner_icon_url)
    return embed

class SelectEditorRoleView(discord.ui.View):
    @discord.ui.select(
        select_type=discord.ComponentType.role_select,
        max_values=1
    )
    async def select_callback(self, select, interaction: discord.Interaction):
        self.disable_all_items()
        GuildAppDB.set_editor_role(str(interaction.guild.id), str(select.values[0].id)) # select.values[0].id is the id of selected role
        await interaction.response.edit_message(content=f"You have selected {select.values[0].mention} as the editor role.\nUsers with this role will have access to the application creation, deletion, editor and actions.", view=None)

class SelectReviewerRoleView(discord.ui.View):
    @discord.ui.select(
        select_type=discord.ComponentType.role_select,
        max_values=1
    )
    async def select_callback(self, select, interaction: discord.Interaction):
        self.disable_all_items()
        GuildAppDB.set_reviewer_role(str(interaction.guild.id), str(select.values[0].id)) # select.values[0].id is the id of selected role
        await interaction.response.edit_message(content=f"You have selected {select.values[0].mention} as the reviewer role.\nUsers with this role will be able to review applications and accept or reject them.", view=None)

class SelectApplicationStartButton(discord.ui.Select):
    async def callback(self, interaction: discord.Interaction):
        self.disabled = True

        embed = discord.Embed(title="**Start your application!**")
        embed.add_field(name=f"Click the button below to start your application for: {self.values[0]}", value="", inline=False)
        embed.set_footer(text="Made by @anorak01", icon_url=owner_icon_url)
        appStartView = ApplicationStartButtonView()

        try:
            message = await interaction.channel.send(embed = embed, view=appStartView)
        except discord.errors.Forbidden:
            await interaction.response.edit_message(content="Missing access to send message", view=None)
            return
        await interaction.response.edit_message(embed=None, content="Application button created", view=None)
        StartButtonDB.add_start_msg(str(message.id), str(self.values[0]), str(interaction.guild.id))

class SelectApplicationOptionsEditor(discord.ui.Select):
    async def callback(self, interaction: discord.Interaction):
        self.disabled = True
        editor = ApplicationEditorView(str(interaction.guild.id), self.values[0])
        embed = get_questions_embed(str(interaction.guild.id), self.values[0])
        await interaction.response.edit_message(embed = embed, view=editor)

class SelectApplicationOptionsRespChannel(discord.ui.Select):
    async def callback(self, interaction: discord.Interaction):
        self.disabled = True
        view = discord.ui.View()
        options = SelectResponseChannel(select_type=discord.ComponentType.channel_select, channel_types=[discord.ChannelType.text], max_values=1, placeholder="Select channel")
        options.set_app_name(self.values[0])
        view.add_item(options)
        await interaction.response.edit_message(view=view)

class SelectResponseChannel(discord.ui.Select):
    def set_app_name(self, app_name):
        self.app_name = app_name

    async def callback(self, interaction: discord.Interaction):
        self.disabled = True
        GuildAppDB.set_response_channel(str(interaction.guild.id), self.app_name, str(self.values[0].id))
        await interaction.response.edit_message(content=f"Selected channel: {self.values[0].mention} for application: {self.app_name}", view=None)

class ApplicationEditorView(discord.ui.View):
    def __init__(self, guild_id, application_name):
        super().__init__(timeout=180)
        self.guild_id = guild_id
        self.application_name = application_name

    @discord.ui.button(
        label="New",
        style=discord.ButtonStyle.green,
        custom_id="editor:add",
        row=0
    )
    async def add_question(self, button: discord.ui.Button, interaction: discord.Interaction):
        modal = AddQuestionModal(self.application_name)
        await interaction.response.send_modal(modal)

    @discord.ui.button(
        label="Remove",
        style=discord.ButtonStyle.red,
        custom_id="editor:remove",
        row=0
    )
    async def remove_question(self, button, interaction: discord.Interaction):
        view = ApplicationEditorView(str(interaction.guild.id), self.application_name)
        options = RemoveQuestionSelect(max_values=1, placeholder="Select question to remove")
        options.set_app_name(self.application_name)
        questions, length = GuildAppDB.get_questions(str(interaction.guild.id), self.application_name)
        if length == 0:
            await interaction.response.edit_message(view=view)
            return
        for i, que in enumerate(questions):
            if len(que) > 100:
                options.add_option(label=f"{str(i+1)}. {que[0:90]}..", value=str(i))
            else:
                options.add_option(label=f"{str(i+1)}. {que}", value=str(i))
        view.add_item(options)
        await interaction.response.edit_message(view=view)

    @discord.ui.button(
        label="Edit",
        style=discord.ButtonStyle.primary,
        custom_id="editor:edit",
        row=0
    )
    async def edit_question(self, button, interaction: discord.Interaction):
        view = ApplicationEditorView(str(interaction.guild.id), self.application_name)
        options = EditQuestionSelect(max_values=1, placeholder="Select question to edit")
        options.set_app_name(self.application_name)
        questions, length = GuildAppDB.get_questions(str(interaction.guild.id), self.application_name)
        if length == 0:
            await interaction.response.edit_message(view=view)
            return
        for i, que in enumerate(questions):
            if len(que) > 90:
                options.add_option(label=f"{str(i+1)}. {que[0:80]}..", value=str(i))
            else:
                options.add_option(label=f"{str(i+1)}. {que}", value=str(i))
        view.add_item(options)
        await interaction.response.edit_message(view=view)

    @discord.ui.button(
        label="Move",
        style=discord.ButtonStyle.gray,
        custom_id="editor:move",
        row=0
    )
    async def move_question(self, button, interaction: discord.Interaction):
        view = ApplicationEditorView(str(interaction.guild.id), self.application_name)
        options = MoveQuestionSelect(max_values=1, placeholder="Select question to move")
        options.set_app_name(self.application_name)
        questions, length = GuildAppDB.get_questions(str(interaction.guild.id), self.application_name)
        if length == 0:
            await interaction.response.edit_message(view=view)
            return
        for i, que in enumerate(questions):
            if len(que) > 100:
                options.add_option(label=f"{str(i+1)}. {que[0:90]}..", value=str(i))
            else:
                options.add_option(label=f"{str(i+1)}. {que}", value=str(i))
        view.add_item(options)
        await interaction.response.edit_message(view=view)


class AddQuestionModal(discord.ui.Modal):
    def __init__(self, app_name):
        self.app_name = app_name
        super().__init__(discord.ui.InputText(label=f"New Question: "), title = "")

    async def callback(self, interaction: discord.Interaction):
        question = self.children[0].value
        if len(question) > 250:
            await interaction.response.send_message(f"Question too long, max 100 characters", ephemeral=True)
            return
        GuildAppDB.add_question(str(interaction.guild.id), self.app_name, question)
        embed = get_questions_embed(str(interaction.guild.id), self.app_name)
        await interaction.response.edit_message(embed=embed)


class RemoveQuestionSelect(discord.ui.Select):
    def set_app_name(self, app_name):
        self.app_name = app_name

    async def callback(self, interaction: discord.Interaction):
        self.disabled = True
        GuildAppDB.remove_question(str(interaction.guild.id), self.app_name, int(self.values[0])+1)
        editor = ApplicationEditorView(str(interaction.guild.id), self.app_name)
        embed = get_questions_embed(str(interaction.guild.id), self.app_name)
        await interaction.response.edit_message(embed = embed, view = editor)


class EditQuestionSelect(discord.ui.Select):
    def set_app_name(self, app_name):
        self.app_name = app_name

    async def callback(self, interaction: discord.Interaction):
        self.disabled = True
        editor = ApplicationEditorView(str(interaction.guild.id), self.app_name)
        modal = EditQuestionModal(self.app_name, int(self.values[0])+1)
        await interaction.response.send_modal(modal)
        await interaction.followup.edit_message(view = editor, message_id=interaction.message.id)

class EditQuestionModal(discord.ui.Modal):
    def __init__(self, app_name, question_index):
        self.app_name = app_name
        self.question_index = question_index
        super().__init__(discord.ui.InputText(label=f"Edited Question: "), title = "")

    async def callback(self, interaction: discord.Interaction):
        question = self.children[0].value
        GuildAppDB.edit_question(str(interaction.guild.id), self.app_name, self.question_index, question)
        embed = get_questions_embed(str(interaction.guild.id), self.app_name)
        await interaction.response.edit_message(embed=embed)


class MoveQuestionSelect(discord.ui.Select):
    def set_app_name(self, app_name):
        self.app_name = app_name

    async def callback(self, interaction: discord.Interaction):
        self.disabled = True
        view = ApplicationEditorView(str(interaction.guild.id), self.app_name)
        options = MoveQuestionSelectNum(max_values=1, placeholder="Select place for move")
        options.set_app_name(self.app_name)
        options.set_init_index(int(self.values[0])+1)
        questions, length = GuildAppDB.get_questions(str(interaction.guild.id), self.app_name)
        for i in range(length):
            options.add_option(label=str(i+1), value=str(i+1))
        view.add_item(options)
        await interaction.response.edit_message(view = view)

class MoveQuestionSelectNum(discord.ui.Select):
    def set_app_name(self, app_name):
        self.app_name = app_name

    def set_init_index(self, init_index: int):
        self.init_index = init_index

    async def callback(self, interaction: discord.Interaction):
        self.disabled = True
        editor = ApplicationEditorView(str(interaction.guild.id), self.app_name)
        GuildAppDB.move_question(str(interaction.guild.id), self.app_name, int(self.init_index), int(self.values[0]))
        embed = get_questions_embed(str(interaction.guild.id), self.app_name)
        await interaction.response.edit_message(view = editor, embed=embed)



def get_actions_embed(guild_id, application, action_type: ActionInteraction) -> discord.Embed:
    embed = discord.Embed(title=f"Application: {application}", description=f"Actions happening on: {action_type.value}")
    actions = GuildAppDB.get_actions(str(guild_id), application, action_type)
    for i, que in enumerate(actions):
        if que["action_type"] == "add_role":
            role = bot.get_guild(int(guild_id)).get_role(que["data"]["role_id"]).name
            embed.add_field(value=f"**{i+1}. {que['display_type']}: {role}**", name="", inline=False)
        else:
            embed.add_field(value=f"**{i+1}. {que['display_type']}**", name="", inline=False)
    embed.set_footer(text="Made by @anorak01", icon_url=owner_icon_url)
    return embed

class ActionAcceptEditorView(discord.ui.View):
    def __init__(self, guild_id, application_name):
        super().__init__(timeout=180)
        self.guild_id = guild_id
        self.application_name = application_name

    @discord.ui.button(
        label="New",
        style=discord.ButtonStyle.green,
        custom_id="action_accept_editor:add",
        row=0
    )
    async def add_action(self, button: discord.ui.Button, interaction: discord.Interaction):
        view = ActionAcceptEditorView(str(interaction.guild.id), self.application_name)
        options = AddActionSelect(max_values=1, placeholder="Select action to add")
        options.set_app_name(self.application_name)
        options.set_action_type(ActionInteraction.ACCEPT)
        for i, que in enumerate(usable_actions):
            options.add_option(label=f"{str(i+1)}. {que}", value=str(usable_actions[que]))
        view.add_item(options)
        await interaction.response.edit_message(view=view)

    @discord.ui.button(
        label="Remove",
        style=discord.ButtonStyle.red,
        custom_id="action_accept_editor:remove",
        row=0
    )
    async def remove_action(self, button, interaction: discord.Interaction):
        view = ActionAcceptEditorView(str(interaction.guild.id), self.application_name)
        options = RemoveActionSelect(max_values=1, placeholder="Select action to remove")
        options.set_app_name(self.application_name)
        actions = GuildAppDB.get_actions(str(interaction.guild.id), self.application_name, action_type=ActionInteraction.ACCEPT)
        options.set_action_type(ActionInteraction.ACCEPT)
        if len(actions) == 0:
            await interaction.response.edit_message(view=view)
            return
        for i, que in enumerate(actions):
            if que["action_type"] == "add_role":
                role = interaction.guild.get_role(que["data"]["role_id"]).name
                options.add_option(label=f"{str(i+1)}. {que['display_type']}: {role}", value=str(i))
            else:
                options.add_option(label=f"{str(i+1)}. {que['display_type']}", value=str(i))
        view.add_item(options)
        await interaction.response.edit_message(view=view)

class ActionDeclineEditorView(discord.ui.View):
    def __init__(self, guild_id, application_name):
        super().__init__(timeout=180)
        self.guild_id = guild_id
        self.application_name = application_name

    @discord.ui.button(
        label="New",
        style=discord.ButtonStyle.green,
        custom_id="action_decline_editor:add",
        row=0
    )
    async def add_action(self, button: discord.ui.Button, interaction: discord.Interaction):
        view = ActionDeclineEditorView(str(interaction.guild.id), self.application_name)
        options = AddActionSelect(max_values=1, placeholder="Select action to add")
        options.set_app_name(self.application_name)
        options.set_action_type(ActionInteraction.DECLINE)
        for i, que in enumerate(usable_actions):
            options.add_option(label=f"{str(i+1)}. {que}", value=str(usable_actions[que]))
        view.add_item(options)
        await interaction.response.edit_message(view=view)

    @discord.ui.button(
        label="Remove",
        style=discord.ButtonStyle.red,
        custom_id="action_decline_editor:remove",
        row=0
    )
    async def remove_action(self, button, interaction: discord.Interaction):
        view = ActionDeclineEditorView(str(interaction.guild.id), self.application_name)
        options = RemoveActionSelect(max_values=1, placeholder="Select action to remove")
        options.set_app_name(self.application_name)
        actions = GuildAppDB.get_actions(str(interaction.guild.id), self.application_name, action_type=ActionInteraction.DECLINE)
        options.set_action_type(ActionInteraction.DECLINE)
        if len(actions) == 0:
            await interaction.response.edit_message(view=view)
            return
        for i, que in enumerate(actions):
            if que["action_type"] == "add_role":
                role = interaction.guild.get_role(que["data"]["role_id"]).name
                options.add_option(label=f"{str(i+1)}. {que['display_type']}: {role}", value=str(i))
            else:
                options.add_option(label=f"{str(i+1)}. {que['display_type']}", value=str(i))
        view.add_item(options)
        await interaction.response.edit_message(view=view)

class AddActionSelect(discord.ui.Select):
    def set_app_name(self, app_name):
        self.app_name = app_name

    def set_action_type(self, action_type):
        self.action_type = action_type

    async def callback(self, interaction: discord.Interaction):
        self.disabled = True
        action = self.values[0]
        if action == "add_role":
            view = discord.ui.View()
            options = SelectRoleToAdd(select_type=discord.ComponentType.role_select, max_values=1, placeholder="Select role to add")
            options.set_app_name(self.app_name)
            options.set_action_type(self.action_type)
            view.add_item(options)
            await interaction.response.edit_message(view=view)

class SelectRoleToAdd(discord.ui.Select):
    def set_app_name(self, app_name):
        self.app_name = app_name

    def set_action_type(self, action_type):
        self.action_type = action_type

    async def callback(self, interaction: discord.Interaction):
        self.disabled = True
        role = self.values[0]
        action = {"result": self.action_type, "action_type": "add_role", "display_type": "Add Role", "data": {"role_id": role.id}}
        GuildAppDB.add_action(str(interaction.guild.id), self.app_name, action)
        if self.action_type == ActionInteraction.ACCEPT:
            editor = ActionAcceptEditorView(str(interaction.guild.id), self.app_name)
            embed = get_actions_embed(str(interaction.guild.id), self.app_name, ActionInteraction.ACCEPT)
        if self.action_type == ActionInteraction.DECLINE:
            editor = ActionDeclineEditorView(str(interaction.guild.id), self.app_name)
            embed = get_actions_embed(str(interaction.guild.id), self.app_name, ActionInteraction.DECLINE)
        await interaction.response.edit_message(embed = embed, view = editor)


class RemoveActionSelect(discord.ui.Select):
    def set_app_name(self, app_name):
        self.app_name = app_name

    def set_action_type(self, action_type: ActionInteraction):
        self.action_type = action_type

    async def callback(self, interaction: discord.Interaction):
        self.disabled = True
        GuildAppDB.remove_action(str(interaction.guild.id), self.app_name, self.action_type, int(self.values[0])+1)
        if self.action_type == ActionInteraction.ACCEPT:
            editor = ActionAcceptEditorView(str(interaction.guild.id), self.app_name)
            embed = get_actions_embed(str(interaction.guild.id), self.app_name, ActionInteraction.ACCEPT)
        if self.action_type == ActionInteraction.DECLINE:
            editor = ActionDeclineEditorView(str(interaction.guild.id), self.app_name)
            embed = get_actions_embed(str(interaction.guild.id), self.app_name, ActionInteraction.DECLINE)
        await interaction.response.edit_message(embed = embed, view = editor)


class SelectActionOptionsEditor(discord.ui.Select):
    async def callback(self, interaction: discord.Interaction):
        self.disabled = True

        view = discord.ui.View()
        options = SelectActionType(max_values=1, placeholder="Select Action™ type")
        options.add_option(label="Accept", value="accept")
        options.add_option(label="Decline", value="decline")
        options.set_app_name(self.values[0])
        view.add_item(options)
        await interaction.response.edit_message(view=view)

class SelectActionType(discord.ui.Select):
    def set_app_name(self, app_name):
        self.app_name = app_name

    async def callback(self, interaction: discord.Interaction):
        self.disabled = True
        if self.values[0] == "accept":
            editor = ActionAcceptEditorView(str(interaction.guild.id), self.app_name)
            embed = get_actions_embed(str(interaction.guild.id), self.app_name, ActionInteraction.ACCEPT)
        if self.values[0] == "decline":
            editor = ActionDeclineEditorView(str(interaction.guild.id), self.app_name)
            embed = get_actions_embed(str(interaction.guild.id), self.app_name, ActionInteraction.DECLINE)
        await interaction.response.edit_message(embed = embed, view=editor)



# View with button that starts the application process
class ApplicationStartButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Start application!",
        style=discord.ButtonStyle.green,
        custom_id=f"persistent:start_application",
    )
    async def start_app(self, button: discord.ui.Button, interaction: discord.Interaction):
        app_name, guild_id = StartButtonDB.get_start_msg(interaction.message.id)

        questions, max_questions=GuildAppDB.get_questions(guild_id, app_name)
        if questions == "error on get questions: application not found":
            await interaction.response.send_message(content="Application no longer exists", ephemeral=True)
            return
        if max_questions == 0:
            await interaction.response.send_message(content="Application doesn't have any questions", ephemeral=True)
            return
        response_channel = GuildAppDB.get_response_channel(guild_id, app_name)

        user = await interaction.user.create_dm()
        embedd = discord.Embed(title=f'{interaction.guild.name} application: {app_name}', description="Hey! Your application has started. You have 300 seconds to complete it.")
        embedd.add_field(value="Please note that answers longer than 1000 characters will be shortened", name="", inline=False)
        embedd.add_field(value=f'You can cancel the application by answering "cancel" to any of the questions', name="", inline=False)
        embedd.set_footer(text="Made by @anorak01", icon_url=owner_icon_url)

        try:
            first_mes = await user.send(embed=embedd)
        except discord.Forbidden:
            await interaction.response.send_message(content="Can't start application. Please allow direct messages from server members in your privacy settings.", ephemeral=True)
            return

        await interaction.response.send_message(content=f"Application started {user.jump_url}", ephemeral=True)

        time_now = time.time()

        application = {'userId': interaction.user.id}

        for i in range(0, max_questions):
            try:
                embed = discord.Embed(title=f'Question [{i+1}/{max_questions}]', description=questions[i])
                await user.send(embed=embed)
                response = await bot.wait_for('message', check=lambda m: m.author == interaction.user and m.channel == user, timeout=300)
                if response.content.startswith("cancel"):
                    await user.send("Your application has been cancelled")
                    return
                else:
                    application[f'question{i}'] = response.content[0:1000]
            except asyncio.TimeoutError:
                await user.send(content="As you haven't replied in 300 seconds, your application has been cancelled")
                return

        channel = bot.get_channel(int(response_channel))

        app_time = time.time() - time_now
        time_rounded = round(app_time, 2)

        #embed_start = discord.Embed(title=f"**{interaction.user.display_name}**'s application for {app_name}") #User:` {interaction.user.display_name}\n`User Mention:` {interaction.user.mention}")

        text_representation = ""
        send_as_file = False

        embed_text_len = 0 # limit 6k characters, but ideally less
        question_embeds = []
        embee = discord.Embed(title=f"**{interaction.user.display_name}**'s application for {app_name}") # create first embed
        for i in range(0, max_questions):
            if embed_text_len > 5000: # if the first embed is full, create new one
                question_embeds.append(embee)
                embee = discord.Embed()
                embed_text_len = 0
                send_as_file = True

            embee.add_field(name=f'{questions[i]}', value=application[f'question{i}'], inline=False)
            embed_text_len += len(questions[i]) + len(application[f'question{i}'])
            text_representation += questions[i] + ":\n" + application[f'question{i}'] + "\n\n"
        question_embeds.append(embee)

        embed_controls = discord.Embed()
        embed_controls.add_field(name="Application statistics", value=f"""
                        `Application duration:` **{time_rounded} seconds**
                        `User mention:` {interaction.user.mention}
                        `User ID:` **{interaction.user.id}**
                        `Account age:` <t:{round(interaction.user.created_at.timestamp())}:R>
                        """)

        embed_controls.set_thumbnail(url=interaction.user.display_avatar.url)
        embed_controls.set_footer(text="Made by @anorak01", icon_url=owner_icon_url)

        question_embeds.append(embed_controls)
        #for embe in question_embeds:
        #    await channel.send(embed=embe)

        appView = ApplicationButtonsView()

        if send_as_file:
            from io import StringIO
            text_file = StringIO(text_representation)
            text_file = discord.File(text_file, filename="application.txt")
            last_msg = await channel.send(content="Application too long to send as message. Sent as file", view=appView, file=text_file, embed=embed_controls)

        else:
            last_msg = await channel.send(embeds=question_embeds, view=appView)

        MessageDB.add_application_msg(last_msg.id, interaction.user.id, interaction.guild.id, app_name)

        await user.send('Thank you for applying!')


# View containing accept and decline buttons for each application
class ApplicationButtonsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Accept",
        style=discord.ButtonStyle.green,
        custom_id=f"persistent:accept",
    )
    async def accept(self, button: discord.ui.Button, interaction: discord.Interaction):
        if is_reviewer_or_admin_func(interaction):
            msg_id = str(interaction.message.id)

            user_id, guild_id, app_name = MessageDB.get_application_msg(msg_id)
            user = await bot.get_or_fetch_user(user_id)
            modal = ApplicationModal(title=f"Accepting: {user.display_name}")
            modal.set_action("acc")
            modal.add_item(discord.ui.InputText(label=f"Reason: "))
            await interaction.response.send_modal(modal)
        else:
            await interaction.response.send_message("You need Administrator permissions or reviewer role to do this.", ephemeral=True)

    @discord.ui.button(
        label="Decline",
        style=discord.ButtonStyle.red,
        custom_id=f"persistent:decline",
    )
    async def decline(self, button: discord.ui.Button, interaction: discord.Interaction):
        if is_reviewer_or_admin_func(interaction):
            msg_id = str(interaction.message.id)

            user_id, guild_id, app_name = MessageDB.get_application_msg(msg_id)

            user = await bot.get_or_fetch_user(user_id)
            modal = ApplicationModal(title=f"Declining: {user.display_name}")
            modal.set_action("dec")
            modal.add_item(discord.ui.InputText(label=f"Reason: "))
            await interaction.response.send_modal(modal)
        else:
            await interaction.response.send_message("You need Administrator permissions or reviewer role to do this.", ephemeral=True)


# Modal functioning as a callback for Accepting/Declining application
class ApplicationModal(discord.ui.Modal):
    def set_action(self, action):
        self.action = action

    async def callback(self, interaction: discord.Interaction):
        reason = self.children[0].value
        msg_id = str(interaction.message.id)
        user_id, guild_id, app_name = MessageDB.get_application_msg(msg_id)
        if self.action == "acc":
            user = await bot.get_or_fetch_user(user_id)
            user = await user.create_dm()
            try:
                await user.send(f"Your application has been accepted!")
            except discord.errors.Forbidden as e:
                await interaction.response.send_message(content="Cannot send messages to this user.\nHe is likely no longer on this server.", ephemeral=True)
                return
            await user.send(f"Reason: {reason}")
            await interaction.response.send_message(content="Application accepted", ephemeral=True)

            actions = GuildAppDB.get_actions(str(guild_id), app_name, ActionInteraction.ACCEPT)
            for i in actions:
                if i["action_type"] == "add_role":
                    role = interaction.message.guild.get_role(int(i["data"]["role_id"]))
                    try:
                        user = await interaction.message.guild.fetch_member(int(user_id))
                    except:
                        print("Can't process action, user not found")
                    try:
                        await user.add_roles(role)
                    except Exception as e:
                        await interaction.followup.send(content=f"I was unable to add role `{role.name}`, I'm missing the permissions")
                else:
                    print("unknown action")

            emb = interaction.message.embeds[0]
            emb.colour = discord.Colour.green()
            embed = discord.Embed(title='Accepted')
            embed.add_field(name="", value=f"`Reason:` {reason}\n`By:` {interaction.user.mention}\n`Time:` <t:{round(time.time())}:f>")
            embed.colour = discord.Colour.green()
            await interaction.followup.edit_message(message_id = interaction.message.id, embeds=[emb, embed])
            view = discord.ui.View.from_message(interaction.message)
            view.disable_all_items()
            await interaction.followup.edit_message(message_id = interaction.message.id, view = view)


        if self.action == "dec":
            user = await bot.get_or_fetch_user(user_id)
            user = await user.create_dm()
            try:
                await user.send(f"Your application has been declined.")
            except discord.errors.Forbidden as e:
                await interaction.response.send_message(content="Cannot send messages to this user.\nHe is likely no longer on this server.", ephemeral=True)
                return
            await user.send(f"Reason: {reason}")
            await interaction.response.send_message(content="Application declined", ephemeral=True)

            actions = GuildAppDB.get_actions(str(guild_id), app_name, ActionInteraction.DECLINE)
            for i in actions:
                if i["action_type"] == "add_role":
                    role = interaction.message.guild.get_role(int(i["data"]["role_id"]))
                    user = interaction.message.guild.get_member(int(user_id))
                    await user.add_roles(role)
                else:
                    print("unknown action")


            emb = interaction.message.embeds[0]
            emb.colour = discord.Colour.red()
            embed = discord.Embed(title='Declined')
            embed.add_field(name="", value=f"`Reason:` {reason}\n`By:` {interaction.user.mention}\n`Time:` <t:{round(time.time())}:f>")
            embed.colour = discord.Colour.red()
            await interaction.followup.edit_message(message_id = interaction.message.id, embeds=[emb, embed])
            view = discord.ui.View.from_message(interaction.message)
            view.disable_all_items()
            await interaction.followup.edit_message(message_id = interaction.message.id, view = view)


try:
    assert(type(TOKEN) == str)
except AssertionError:
    print("you need to set up a token")
# end
bot.run(TOKEN)
