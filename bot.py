# -*- coding: UTF-8 -*-

import discord
import asyncio
import os
import yaml
import sys
import datetime
import time
import io

try:

   import cPickle as pickle

except:

   import pickle

# Discord API bot token
TOKEN = 'EXAMPLE'

# ID of the bot's admin
DEV_ID = ''

# ID's (find them in Discord's developer mode) for the master server and the channel within that server, that it should post to.
MASTER_SERVER_ID = ''
MASTER_CHANNEL_ID = ''

class ChanLinkBot(discord.Client):
    ############
    ### Initialization
    ############    
    def __init__(self):
        super(ChanLinkBot, self).__init__()

        self._data = {
            'command_prefixes': ['cl!', '<#'],
            'command_mapping': {
                'restart': [],
                'debug': [],
                'post_update': ['update description'],
                'dev_move': ['channel to move to'],
                'servers': [],
                
                'ping': [],            
                'about': [],
                'invite': [],
                'help': [],
                
                #'list': ['type of item'],
                #'add': ['type of item', 'name'],
                #'delete': ['type of item', 'number'],

                'markers': [],
                'marks': [],
                'mark': ['description'],
                'mark_by_id': ['ID', 'description'],
                'del_marker': ['marker number'],
                'pins': [],
                'pin': ['description'],
                'del_pin': ['marker number'],
                
                'move': ['channel to move to'],
                'go': ['channel to move to'],
                
                'capture': ['name', 'number of lines to capture'],
                'capture_channel': [],
                'logs': [],
                'log': ['log number'],
                'del_log': ['log number'],
                'wipe_messages': ['number of messages to wipe'],

                'active_channels': [],
            },
            
            'bot_admin_id': DEV_ID,
            'master_server_id': MASTER_SERVER_ID,
            'master_channel_id': MASTER_CHANNEL_ID,
            'master_channel': False,
            'update_channel_id': 602073313199652885,
            'invite_link': "https://discordapp.com/oauth2/authorize?client_id=601713723652046867&scope=bot&permissions=536964096",
            'embed_colour': discord.Colour.blue(),
            'automatic_replace_exception_servers': {
            	'DiscordPy': 336642139381301249
            }
        }
        self._channel_activity_tracker = {}
            
        self._data['database'] = {}
        self._load_data()

    ############
    ### Misc methods
    ############ 
    # Messages for debugging and monitoring purposes
    async def _dev_message(self, msg_type, msg_content, channel=False, public=False):
        msg_parts = []
        msg_parts.append("[**%s**]" % msg_type.upper())

        if channel:
            msg_parts.append("[_%s_]" % (channel.guild.name))

        msg_parts.append(msg_content)

        msg = ' '.join(msg_parts)
        console_msg_parts = msg_parts
        console_msg_parts[0] = console_msg_parts[0].replace("**", "")
        console_msg = ' '.join(console_msg_parts)

        print(console_msg)

        if self._data['master_channel']:
            await self._data['master_channel'].send(msg)
        
        if channel and public:
            public_msg_parts = msg_parts
            public_msg_parts.pop(1)
            public_msg = ' '.join(public_msg_parts)

            await channel.send(public_msg)

        return

    def _user_is_dev(self, author):
        if author.id == self._data['bot_admin_id']:
            return True
        
        return False

    def _user_is_staff(self, author):
        #if author.id == self._data['bot_admin_id']:
            #return True
        if author.guild_permissions.kick_members:
            return True
        
        return False
    
    def _slice_output(self, text):
        """Slices a string into chunks of 1900 a piece, which is Discord's character limit per message"""
        
        return [text[i:i+1900] for i in range(0, len(text), 1900)]
    
    def _to_singular(self, word):
        if word.endswith('s'):
            word = word[:-1]
            
        return word
    
    def _to_plural(self, word):
        if not word.endswith('s'):
            word += 's'
            
        return word
    
    ############
    ### Input management
    ############
    def _split_command(self, command_string):
        return command_string.split(' ')
    
    ############
    ### Data management
    ############
    def _save_data(self):
        try:
            pickle_string = pickle.dumps(self._data['database'])
        except Exception as e:
            print(e)
            print("[FATAL ERROR] Failed to save database. Save aborted, data secure!")
            self._load_data() 
            
            return False

        with open('chanlink.pckl', 'wb') as fh:
            fh.write(pickle_string)
            
        return True
    
    def _load_data(self):
        if not os.path.exists('chanlink.pckl'):
            with open('chanlink.pckl', 'wb') as fh:
                fh.write('')
        
        try:
            self._data['database'] = pickle.load(open('chanlink.pckl', 'rb'))
        except EOFError:
            self._data['database'] = {}

        return True

    def _prep_user_data(self, message_object, category=False):
        if 'user_data' not in self._data['database'][message_object.channel.guild.id].keys():
            self._data['database'][message_object.channel.guild.id]['user_data'] = {}
            
        if message_object.author.id not in self._data['database'][message_object.channel.guild.id]['user_data']:
            self._data['database'][message_object.guild.id]['user_data'][message_object.author.id] = {}
        
        if not category:
            pass
        else:
            if category not in self._data['database'][message_object.channel.guild.id]['user_data'][message_object.author.id].keys():
                self._data['database'][message_object.channel.guild.id]['user_data'][message_object.author.id][category] = []
                
        return self._save_data()
                
    def _get_user_data(self, message_object, category=False):
        return self._data['database'][message_object.channel.guild.id]['user_data'][message_object.author.id][category]
    
    def _get_user_data_item(self, message_object, category, *query):
        data = self._get_user_data(message_object, category)
        
        item = False
        if query[0].isnumeric():
            item_id = int(query[0])-1
            if item_id >= len(data):
                return False
            
            item = data[item_id]
            
            return item
        else:
            for i_item in data:
                if i_item['name'] == ' '.join(query):
                    item = i_item
                    
            if not item:
                return False
            
            return item
            
        return
    
    def _list_user_data(self, message_object, category):
        pass
    
    async def _add_user_data(self, message_object, category, item):
        self._prep_user_data(message_object, category)
        
        self._data['database'][message_object.channel.guild.id]['user_data'][message_object.author.id][category].append(item)
        
        result = self._save_data()
        if not result:
            await self._dev_message("fatal error", "Failed to save the database, this means what you were trying to do has been aborted. The developer has been notified!", channel=message_object.channel, public=True)
            await self._dev_message("fatal error", "Failed to save the database! User %s executed command \"%s\" in channel %s." % (message_object.author.name, message_object.clean_content, message_object.channel.name), channel=message_object.channel)

            return False
        
        return True
    
    async def _del_user_data(self, message_object, category, item_index):
        if item_index < 0:
            return False
        
        try:
            del(self._data['database'][message_object.channel.guild.id]['user_data'][message_object.author.id][category][item_index])
        except:
            return False
        
        result = self._save_data()
        if not result:
            await self._dev_message("fatal error", "Failed to save the database, this means what you were trying to do has been aborted. The developer has been notified!", channel=message_object.channel, public=True)
            await self._dev_message("fatal error", "Failed to save the database! User %s executed command \"%s\" in channel %s." % (message_object.author.name, message_object.clean_content, message_object.channel.name), channel=message_object.channel)

            return False

        return True
        
    ############
    ### Events 
    ############
    async def on_ready(self):
        # Initialize more data
        self._data['avatar'] = await self.user.avatar_url.read()
        self._data['master_channel'] = self.get_guild(self._data['master_server_id']).get_channel(self._data['master_channel_id'])
        
        # Create the database
        for guild in self.guilds:
            if guild.id not in self._data['database']:
                self._data['database'][guild.id] = {
                    'settings': [],
                    'user_data': {}
                }
                    
        await self._dev_message('system', "ChanLink started.")

    async def pop_channel_activity_tracker(client):
        await client.wait_until_ready()
        await client._dev_message("channel_activity_tracker", "started")

        while True:
            for guild_id in client._channel_activity_tracker.keys():
                for channel_id in client._channel_activity_tracker[guild_id].keys():
                    item_index = 0
                    for message in client._channel_activity_tracker[guild_id][channel_id]:
                        # If the message date is older than 3 minutes, delete the channel tracker item
                        date_difference = datetime.datetime.now()-message.created_at
                        if date_difference.seconds > 180:
                            del client._channel_activity_tracker[guild_id][channel_id][item_index]
                            tmp_guild = client.get_guild(guild_id)
                            tmp_chan = tmp_guild.get_channel(channel_id)

                        item_index += 1

            await asyncio.sleep(1)

    async def on_message(self, message):
        # We do not want the bot to reply to itself
        if message.author == self.user:
            return

        # Track the message frequency for use in the "most active channel" request. We do not use the database for this as this data is useless to save permanently.
        if message.channel.guild.id not in self._channel_activity_tracker.keys():
            self._channel_activity_tracker[message.channel.guild.id] = {}
        if message.channel.id not in self._channel_activity_tracker[message.channel.guild.id].keys():
            self._channel_activity_tracker[message.channel.guild.id][message.channel.id] = []

        # Append the item to the list and add a task that deletes said item after N seconds (amount of seconds is defined in pop_channel_activity_tracker_item())
        self._channel_activity_tracker[message.channel.guild.id][message.channel.id].append(message)

        split_command = self._split_command(message.content)
        command = split_command[0].lower()

        # Natural-language commmands
        chanlink_mentioned = False
        for user in message.mentions:
            if user.id == self.user.id:
                chanlink_mentioned = True

        if command == "chanlink," or chanlink_mentioned:
            given_phrase = ' '.join(split_command[1:])

            for phrase in ['is anyone here', 'anyone', 'where are', 'is there activity', 'is there anyone', 'is anyone chatting', 'is anyone active', 'is the server dead', 'is this place dead', 'is this server dead', 'i solemnly swear i\'m up to no good', 'i solemnly swear i am up to no good', 'map', 'show me where everyone is']:
                if given_phrase.lower().startswith(phrase):
                    await self._cmd_active_channels(message)
            for phrase in ['where is']:
                if given_phrase.lower().startswith(phrase):
                    target_name = ' '.join(split_command[3:]).replace('?', '')
                    if target_name in ['everyone', 'everybody']:
                        await self._cmd_active_channels(message)
        
        command_no_prefix = command
        for prefix in self._data['command_prefixes']:
            command_no_prefix = command_no_prefix.replace(prefix, '')
            
        arguments = split_command[1:]
        
        prefix_found = False
        for prefix in self._data['command_prefixes']:
            if command.startswith(prefix):
                prefix_found = True
        
        if not prefix_found:
            return
        
        if command_no_prefix in self._data['command_mapping'].keys():
            index = 0
            for argument in self._data['command_mapping'][command_no_prefix]:
                if index >= len(arguments):
                    await message.channel.send("Please provide a %s" % (argument))
                    return
                index += 1
                
        for mapped_command in self._data['command_mapping'].keys():
            if command_no_prefix == mapped_command:
                try:
                    target_func = getattr(self, "_cmd_%s" % (mapped_command))
                except AttributeError:
                    await self._dev_message('error', 'Function _cmd_%s did not exist in our class..' % (mapped_command), channel=message.channel)
                    return 
                
                await target_func(message, *arguments)
        
        if message.content.startswith('<#'):
            # TODO: Add per-server setting that enables or disables the triggering of cl!go by posting a channel name
            if message.channel.guild.id in list(self._data['automatic_replace_exception_servers'].values()):
                return
            
            if len(message.content.split(" ")) == 1:
                if message.channel_mentions:
                    if message.channel_mentions[0].id != message.channel.id:
                        if self._user_is_staff(message.author):
                            await self._dev_message('channel_link', "Shorthand used by staff.", channel=message.channel)
                            await self._cmd_move(message)
                        else:
                            await self._dev_message('channel_link', "Shorthand used by a member.", channel=message.channel)
                            await self._cmd_go(message)

        return

    async def on_guild_join(self, guild):
        if guild.system_channel:
            await guild.system_channel.send("""
Hi! Thanks for adding me to your server. Type `cl!help` to learn how to use me.

I need to be in all the public channels of your server for everything to work correctly. You don't need to give me administrator or moderator rights. I don't need to be in admin/mod-only channels.

Any time you want to move a discussion from one channel to another, use my command `cl!move`, instead of simply asking everyone to move. This will give you the benefits of channel links. Type `cl!about` to learn more about the purpose of ChanLink and channel links.
            """)

            await self._dev_message('server_add', "I got added to server \"%s\", server ID: %s. Owner is %s#%s." % (guild.name, guild.id, guild.owner.name, guild.owner.discriminator))

        return

    async def on_guild_remove(self, guild):
        await self._dev_message('server_removed', "I got removed from server \"%s\", server ID: %s. Owner is %s#%s." % (guild.name, guild.id, guild.owner.name, guild.owner.discriminator))

        return
    
    ############
    ### Core data list management commands
    ############
    async def _add(self, message, item_type, *args):
        target_func = False
        
        try:
            target_func = getattr(self, "_add_%s" % (self._to_singular(item_type)))
        except AttributeError:
            await message.channel.send("That is not something you may add.")
            return
        
        if target_func:
            status = await target_func(message, *args)
        
        if status:
            await message.channel.send("The %s was successfully added." % (self._to_singular(item_type)), delete_after=2)
        
        #await message.delete()
        
        return    

    async def _delete(self, message, item_type, target_index):
        target_index = int(target_index)-1
        
        target_data_list = self._get_user_data(message, self._to_plural(item_type))
        if len(target_data_list) <= target_index:
            await message.channel.send("That item does not exist.")
            return
        
        # Add extra functionality if needed via a method
        target_func = False
        try:
            target_func = getattr(self, "_del_%s" % (self._to_singular(item_type)))
        except AttributeError:
            pass
        
        if target_func:
            await target_func(message, target_index)
        
        # Actual deletion
        status = await self._del_user_data(message, self._to_plural(item_type), target_index)
        if status == False:
            await self._dev_message('error', 'Failed to delete a %s' % (self._to_singular(item_type)))
            return
        
        await message.channel.send("The %s was successfully deleted." % (self._to_singular(item_type)))
        
        await message.delete()
        
        return
    
    async def _list(self, message, item_type):
        # Ohhh dear
        target_func = False
        
        try:
            target_func = getattr(self, "_list_%s" % (item_type))
        except AttributeError:
            await message.channel.send("That is not an existing list.")
            return
        
        if target_func:
            await target_func(message, self._get_user_data(message, item_type))
            
        return

    ############
    ### Extra data management functionality
    ############
    async def _add_marker(self, message, *args):
        """Create a personal marker"""

        marker_desc = ' '.join(args)

        marker = {
            'channel_id': message.channel.id,
            'message_id': message.id,
            'description': marker_desc
        }

        result = await self._add_user_data(message, 'markers', marker)
        if not result:
            return False

        await message.add_reaction(u"🚩")

        await self._dev_message('channel_link', "A member created a personal marker.", channel=message.channel, public=False)
        
        return
           
    async def _list_markers(self, message, markers):
        if not markers:
            await message.channel.send("You don't have any markers set up yet. Use cl!mark to add one.")
            return
        
        markers_strings = []
        counter = 1
        for marker in markers:
            jump_url = "http://discordapp.com/channels/%s/%s/%s" % (message.channel.guild.id, marker['channel_id'], marker['message_id'])
            markers_strings.append("%i) %s \[[Jump](%s)\]" % (counter, marker['description'], jump_url))
            
            counter += 1
        del(counter)
        
        # Send the list of markers in chunks of 10 a message
        counter = 1
        total_index = 0
        first_msg_posted = False
        marker_strings_collected = []
        for marker_string in markers_strings:
            marker_strings_collected.append(marker_string)
            
            if counter >= 10 or total_index >= len(markers_strings)-1:
                marker_embed = discord.Embed(
                    description="\n".join(marker_strings_collected),
                    color=self._data['embed_colour']
                )
                
                if not first_msg_posted:
                    marker_embed.title = "Your markers"
                
                await message.channel.send(embed=marker_embed)
                
                if not first_msg_posted:
                    first_msg_posted = True
                marker_strings_collected = []
                counter = 1
            
            counter += 1
            total_index += 1
        
        return

    async def _del_marker(self, message, marker_index):
        markers = self._get_user_data(message, 'markers')

        channel_id = markers[marker_index]['channel_id']
        message_id = markers[marker_index]['message_id']
        
        marker_channel = await self.fetch_channel(channel_id)
        
        marker_message = await marker_channel.fetch_message(message_id)
        
        index = 0
        for reaction in marker_message.reactions:
            if reaction.me:
                if reaction.emoji == "🚩":
                    await marker_message.reactions[index].remove(message.channel.guild.me)
            
            index += 1
        del(index)
        
        await marker_message.delete()
        
        return
    
    async def _add_log(self, message, *args):
        """Capture the last N lines of conversation, like a screenshot"""
        
        if not self._user_is_staff(message.author) and not self._user_is_dev(message.author):
            await message.channel.send("Only staff is allowed to capture logs.")
            return
        
        name = args[0]
        amt_to_capture = int(args[1])
        amt_to_capture += 2 # Take into account command messages
        
        if (amt_to_capture > 9999999):
            await message.channel.send("Nice try, no flooding ChanLink please.")
            return False
        
        capture_message = await message.channel.send("Capturing..")
        await self._dev_message('log_capture', "Capturing log..", channel=message.channel)
        
        captured = await message.channel.history(limit=amt_to_capture).flatten()
        # Get rid of the command messages
        captured.pop(0)
        captured.pop(0)
        captured.reverse()
        
        captured_serializable = []
        for message_raw in captured:
            attachments = []

            if message_raw.attachments:
                for attachment in message_raw.attachments:
                    attachments.append(attachment.url)

            message_dict = {
                'author_id': message_raw.author.id,
                'author_name': message_raw.author.name,
                'author_discriminator': message_raw.author.discriminator,
                'datetime': str(message_raw.created_at.strftime('%d-%m-%y | %H:%M')),
                'content': message_raw.clean_content,
                'attachments': attachments
            }
            
            captured_serializable.append(message_dict)
        
        result = await self._add_user_data(message, 'logs', 
            {
                'name': name,
                'date': str(datetime.datetime.now().strftime("%d-%m-%Y %H:%M")),
                'server_name': message.channel.guild.name,
                'channel_name': message.channel.name,
                'messages': captured_serializable
            }
        )
        if not result:
            return False
        
        await self._dev_message('log_capture', "Capture complete.", channel=message.channel)
            
        await capture_message.delete()
        
        await message.delete()
        
        return
    

    async def _add_full_log(self, message, *args):
        """Capture a full log of a specified channel"""
        
        if not self._user_is_staff(message.author) and not self._user_is_dev(message.author):
            await message.channel.send("Only staff is allowed to capture logs.")
            return

        name = "#%s_%s" % (message.channel.name, str(datetime.datetime.now().strftime('%H-%M_%d-%m-%y')))
        
        capture_message = await message.channel.send("Capturing full channel log. This could take a while, please be patient..")
        await self._dev_message('log_capture', "Capturing full channel log..", channel=message.channel)
        
        chan_history = message.channel.history(limit=None)

        captured_serializable = []
        async for message_raw in chan_history:
            attachments = []

            if message_raw.attachments:
                for attachment in message_raw.attachments:
                    attachments.append(attachment.url)

            message_dict = {
                'author_id': message_raw.author.id,
                'author_name': message_raw.author.name,
                'author_discriminator': message_raw.author.discriminator,
                'datetime': str(message_raw.created_at.strftime('%d-%m-%y | %H:%M')),
                'content': message_raw.clean_content,
                'attachments': attachments
            }
            
            captured_serializable.insert(0, message_dict)

        captured_serializable.pop(-1)
        captured_serializable.pop(-1)
        
        result = await self._add_user_data(message, 'logs', 
            {
                'name': name,
                'date': str(datetime.datetime.now().strftime("%d-%m-%Y %H:%M")),
                'server_name': message.channel.guild.name,
                'channel_name': message.channel.name,
                'messages': captured_serializable
            }
        )
        if not result:
            return False
        
        await message.channel.send("Capture complete. View your log in cl!logs")
        await self._dev_message('log_capture', "Capture complete.", channel=message.channel)
        
        return


    async def _list_logs(self, message, logs):        
        if not self._user_is_staff(message.author) and not self._user_is_dev(message.author):
            await message.channel.send("Only staff is allowed to capture logs.")
            return
        
        if not logs:
            await message.channel.send("You have no logs yet. Use cl!capture to make some.")
            return
            
        index = 1
        output = ""            
        for log in logs:
            output += "%s) %s\n" % (index, log['name'])
            index += 1
            
        await message.channel.send(embed=discord.Embed(
            title="Your captured logs",
            description=output
        ))
        
        return

    ############
    ### Data Management Aliases
    ############
    async def _cmd_markers(self, message, *args):
        return await self._list(message, 'markers')
    async def _cmd_marks(self, message, *args):
        return await self._list(message, 'markers')
    async def _cmd_mark(self, message, *args):
        return await self._add(message, 'markers', *args)
    async def _cmd_del_marker(self, message, *args):
        return await self._delete(message, 'markers', *args)
    async def _cmd_pins(self, message, *args):
        return await self._list(message, 'markers')
    async def _cmd_pin(self, message, *args):
        return await self._add(message, 'markers', *args)
    async def _cmd_del_pin(self, message, *args):
        return await self._delete(message, 'markers', *args)
    async def _cmd_logs(self, message, *args):
        return await self._list(message, 'logs')
    async def _cmd_capture(self, message, *args):
        return await self._add(message, 'logs', *args)
    async def _cmd_capture_channel(self, message, *args):
        return await self._add(message, 'full_logs', *args)
    async def _cmd_del_log(self, message, *args):
        return await self._delete(message, 'logs', *args)
 
    ############
    ### Misc. Commands
    ############   
    async def _cmd_restart(self, message):
        """Restart the bot"""

        # TODO: Add reload without restart

        if not self._user_is_dev(message.author):
            await message.channel.send("Only the bot's creator is allowed to use this command.")
            return

        await self._dev_message('system', "Restarting...", channel=message.channel, public=False)

        # Clear all webhooks
        try:
            hooks = await message.guild.webhooks()
            
            for hook in hooks:
                await hook.delete()
        except:
            pass
        
        await message.delete()

        await self.close()
        sys.exit(0)

    async def _cmd_debug(self, message):
        """Command meant for debugging whatever"""

        if not self._user_is_dev(message.author):
            await message.channel.send("Only the bot's creator is allowed to use this command.")
            return

        await self._dev_message('PUNISHED', 'I have placed myself in an incinerator and will now appropriately burn in excruciating pain for pinging my creator almost every second with annoying notifications. I hope my creator forgives me.', channel=message.channel, public=True)

        return
    
    async def _cmd_ping(self, message):
        await message.channel.send("Pong!", delete_after=2)
        await message.delete()
        
        return

    async def _cmd_servers(self, message):
        """List all servers the bot is in"""

        if not self._user_is_dev(message.author):
            await message.channel.send("Only the bot's creator is allowed to use this command.")
            return

        guild_names = []
        for guild in self.guilds:
            guild_names.append("%s (owned by *%s\#%s*)" % (guild.name, guild.owner.name, guild.owner.discriminator))

        await message.channel.send("\n".join(guild_names))
        return

    async def _cmd_about(self, message):
        await message.channel.send("""
**
Created by: Rose22 (on github)
Current admin: %s

ChanLink lets server staff (administrators, moderators, and so on) move conversations between channels, whilst creating links between the two conversations, to help you keep track of what moves where. When later on, you're reading the message history of a channel, this lets you easily jump to and from the points where a conversation moved from one channel to another. This then essentially links conversations across channels.

A Channel Link is a set of two messages across two channels, both of which contain a link, that lead directly to the other message in the set, respectively. Clicking such a link will make Discord jump to the message, as if you clicked the "jump" button in the Discord search bar. It's like a "portal" to the next part of the conversation. When a moderator uses a ChanLink Move (cl!move), it posts a message in the channel everyone is to move to, that marks the spot (in the message history) where a conversation got moved. It also posts a message in the channel the command was issued in, that contains the link that lets you go directly to that spot using Discord jump functionality.

It's a bit of a difficult concept to explain in text - it's better to just see for yourself. And seeing it for yourself is easy: just use cl!move, and it will probably all make sense.

_Type cl!help for information on how to use ChanLink._
    """ % self._data['bot_admin_id'])

        await self._dev_message('about', "Someone used the about command :)", channel=message.channel, public=False)

        return

    async def _cmd_invite(self, message):
        """Send an invite to the issuer of the command, that adds ChanLink to their server"""

        await message.channel.send("Use this link to invite me to your own server: %s" % self._data['invite_link'])
        await self._dev_message('invite', "Someone requested an invite link!", channel=message.channel, public=False)

        return

    async def _cmd_help(self, message):
        """Display help"""

        help_text = """
Here's how to use ChanLink:

_Usable by administrators and moderators only:_
> **cl!move <channel>**: Moves the conversation to the specified channel. (Example: cl!move #vent)

> **cl!wipe_messages <number>**: Deletes <number> ChanLink messages from the channel you use this command in. Use "all" as the number to wipe all ChanLink messages from a channel. ___Irreversible, use with caution.___

> **cl!capture** <name> <amount>: Captures a log of the most recent messages that were said. Amount defines how many messages you want to capture.
> **cl!logs**: List all logs that you captured
> **cl!log** <number>: Retrieve a log. Use the number of the log as shown in cl!logs
> **cl!del_log**: Delete a log. Use the number of the log as shown in cl!logs

_Usable by anyone_:
> **cl!go**: Go to another channel. It's like a more discreet version of cs!move, usable by non-staff. For when you want to take a conversation you're having, to another channel. If the server has it enabled, you can also just type the channel name and hit enter to accomplish the same thing as cl!go.

> **cl!mark <description>**: Create a marker. A marker is like a discord Pin, except you can pin messages without being staff. It anchors the marker to the message you sent to create the marker. Example: cl!mark my marker
> **cl!markers**: Show a list of your markers, that lets you jump/teleport to any of the markers you've added.
> **cl!del_marker**: Delete a marker. Use the number of the marker as shown in cl!markers

> **cl!about**: About ChanLink, what ChanLink is and what it's for, and it's creator.
> **cl!invite**: Get a link to invite ChanLink to your server!
> **cl!help**: This help message.
        """

        await message.channel.send(help_text)

        return

    async def _cmd_active_channels(self, message):
        # Pop the last entry in the channel tracker, since that's the message that was just posted.. >.>
        del self._channel_activity_tracker[message.guild.id][message.channel.id][-1]

        find_active = {}
        for channel_id in self._channel_activity_tracker[message.guild.id].keys():
                channel_activity = len(self._channel_activity_tracker[message.guild.id][channel_id])
                if channel_activity > 0:
                    # Don't include channels the user doesn't have access to
                    if not message.author.permissions_in(message.channel).read_messages or not message.guild.me.permissions_in(message.channel).read_messages:
                        continue

                    find_active[channel_id] = channel_activity

        if not find_active:
            await message.channel.send("No one's active at the moment.. you could be the one to start something up again!", delete_after=10)

            if message.guild.me.permissions_in(message.channel).manage_messages:
                await asyncio.sleep(10)
                await message.delete()
            return

        # Sort by amount of activity
        find_active_sorted = sorted(find_active.items(), key=lambda x: x[1], reverse=True)

        msg_strs = []
        for channel_id, activity in find_active_sorted:
            activity_percentage = (activity/20)*100
            if activity_percentage > 100: 
                activity_percentage = 100

            tmp_channel = message.channel.guild.get_channel(channel_id)
            msg_strs.append("[#%s](%s) (%d%% active)" % (tmp_channel.name, tmp_channel.last_message.jump_url, activity_percentage))

        msg_str = "Everyone's currently chatting in: %s" % (', '.join(msg_strs))

        msg_embed=discord.Embed(description=msg_str)

        await message.channel.send(embed=msg_embed)
        #await message.channel.send(embed=msg_embed, delete_after=30)
        
        #if message.guild.me.permissions_in(message.channel).manage_messages:
            #await asyncio.sleep(30)
            #await message.delete()

        return

# People thought this was creepy, so it was removed.
# ---
#    async def _cmd_find(self, message, target_name):
#        del self._channel_activity_tracker[message.guild.id][message.channel.id][-1]
#
#        found = {}
#        found_name = ""
#        for channel_id, messages in self._channel_activity_tracker[message.guild.id].items():
#            for tracker_message in messages:
#                tracker_message_nick = ""
#                if hasattr(tracker_message.author, "nick"):
#                    if isinstance(tracker_message.author.nick, str):
#                        tracker_message_nick = tracker_message.author.nick
#
#                tracker_message_nick = tracker_message.author.nick if isinstance(tracker_message.author.nick, str) else ""
#
#                if target_name.lower() in tracker_message.author.name.lower():
#                    found[tracker_message.channel.name] = tracker_message
#                    found_name = tracker_message.author.name
#                if target_name.lower() in tracker_message_nick.lower():
#                    found[tracker_message.channel.name] = tracker_message
#                    found_name = tracker_message.author.nick
#
#        if not found:
#            await message.channel.send("%s is currently not active in this server." % (target_name.capitalize()))
#            return
#
#        found_list = []
#        for channel_name, tracker_message in found.items():
#            found_list.append("[#%s](%s)" % (channel_name, tracker_message.jump_url))
#
#        await message.channel.send(
#            embed=discord.Embed(
#                description="%s is currently active in: %s" % (found_name, ', '.join(found_list))
#            )
#        ) 
#

    async def _cmd_post_update(self, message, msg_content):
        await self._dev_message('update_posted', "Posting update to all update channels: %s" % (msg_content), channel=message.channel, public=True)

        for guild in self.guilds:
            found_chan = False
            for channel in guild.text_channels:
                if channel.name == "chanlink_updates":
                    found_chan = True
                    await channel.send("UPDATE: %s" % (msg_content))
                    await self._dev_message('update_posted', "Posted update message to update channel in server %s" % (guild.name), channel=message.channel, public=True)

            if not found_chan:
                await self._dev_message('update_posted', "Server %s does not have a #chanlink_updates channel." % (guild.name), channel=message.channel, public=True)

        await self._dev_message('update_posted', "Done posting update.", channel=message.channel, public=True)

        return


    async def _cmd_move(self, message, filler=False):
        """The main functionality. We create a two-way path, where one message links to the other and vice versa, in order to create a "portal" between two messages."""

        if not message.channel_mentions:
            await message.channel.send("Please specify a channel to move to.")
            return
        
        if message.channel_mentions[0].id == message.channel.id:
            await message.channel.send("You just tried to link to the channel you're in right now. You're silly.")
            return

        if not self._user_is_staff(message.author):
            await message.channel.send("Only staff is allowed to use this command.")
            return

        # Determine the source channel (where we get sent from) and the target channel (where we get sent to)
        target_chan = message.channel_mentions[0]
        src_chan = message.channel

        # Create the target endpoint of the channel link
        target_embed = discord.Embed(
            title='Channel Link',
            description="Conversation moved from #%s to #%s by staff." % (src_chan.name, target_chan.name),
            color=self._data['embed_colour']
        )
        target_msg = await target_chan.send(embed=target_embed)

        # Create the source endpoint of the channel link
        src_msg = await src_chan.send(embed=discord.Embed(title='Channel Link', color=self._data['embed_colour'], description="A member of staff has requested that you move your conversation to #%s.\n\n[Please go there now. Click or tap here to move.](<%s>)" % (target_chan.name, target_msg.jump_url)))

        # Now create the second link, that points back to the source endpoint, and add it to the target endpoint.
        target_embed.description += "\n\n[Click here to go to the point where the conversation was moved.](<%s>)" % (src_msg.jump_url)
        await target_msg.edit(embed=target_embed)

        await self._dev_message('channel_link', "Staff moved a discussion to another channel.", channel=message.channel, public=False)

        return
    
    async def _cmd_go(self, message, filler=False):
        """User version of cl!move. More discreet."""

        if not message.channel_mentions:
            await message.channel.send("Please specify a channel to move to.")
            return
        
        if message.channel_mentions[0] == message.channel:
            return

        # Determine the source channel (where we get sent from) and the target channel (where we get sent to)
        target_chan = message.channel_mentions[0]
        src_chan = message.channel

        # Create the target endpoint of the channel link
        try:
            target_msg = await target_chan.send("loading..")
            #await self._dev_message('debug', "%s tried to link to channel #%s from channel #%s" % (message.author.name, target_chan.name, src_chan.name), channel=message.channel)
        except:
            await message.add_reaction(u"⛔")
            return

        # Create the source endpoint of the channel link
        try:
            src_msg = await src_chan.send(embed=discord.Embed(description="[@%s has linked to #%s. Click here to go there. ](<%s>)" % (message.author.name, target_chan.name, target_msg.jump_url), colour=self._data['embed_colour']))
        except:
            await self._dev_message('debug', "Something went wrong while sending the message into the source endpoint channel.", channel=message.channel)
            await target_msg.delete()
            return

        # Now create the second link, that points back to the source endpoint, and add it to the target endpoint.
        target_embed = discord.Embed(
            description="[@%s linked to this channel from #%s. Click here to return.](<%s>)" % (message.author.name, message.channel.name, src_msg.jump_url),
            color=self._data['embed_colour']
        )
        try:
            await target_msg.edit(embed=target_embed, content="")
        except:
            # Possible fix:
            #await target_msg.delete()
            await self._dev_message('debug', "Something went wrong while editing the message in the target endpoint channel.", channel=message.channel)
        
        # Delete the command message
        await message.delete()

        await self._dev_message('channel_link', "A member linked to another channel.", channel=message.channel, public=False)

        return
                
    async def _cmd_log(self, message, *args):
        log = self._get_user_data_item(message, 'logs', *args)
        if not log:
            await message.channel.send("That log doesn't exist.")
            return
        
        status_message = await message.channel.send("Loading..")
        
        output_raw = ""

        output = ""
        
        for msg in log['messages']:
            if msg['attachments']:
                if msg['content']:
                    msg['content'] += " "

                msg['content'] += " | ".join(msg['attachments'])

            output += "[%s] <%s> %s\n" % (msg['datetime'], msg['author_name'], msg['content'])
        
        if len(output) <= 2000:
            # Display a screenshot-like view instead of sending a file
            output = output.replace('>', '\>')
            
            await message.channel.send(embed=discord.Embed(title="Your capture", description=output))
            await status_message.delete()
            
            return
        else:
            # Send as a text file
            output = "--- LOG BEGIN [Date Captured: %s] [Server: %s] [Channel: #%s] [Messages: %d] ---\n" % (log['date'], log['server_name'], log['channel_name'], len(log['messages'])) + output
            output += "--- LOG END ---\n"
            
            log_virtual_file = io.StringIO(output)
            discord_file = discord.File(fp=log_virtual_file, filename="log_%s.txt" % (log['name']))
            
            try:
                await message.channel.send(content="Here's your log.", file=discord_file)
            except discord.errors.HTTPException:
                # Log's too big to send, we need to split it into parts

                await message.channel.send("That log is pretty big. Sending it in parts..")

                log_virtual_file.seek(0)

                part_counter = 1
                while True:
                    buf = log_virtual_file.read(8000000) # Chunks of 7mb each
                    if not buf:
                        break

                    log_chunk = io.StringIO(buf)

                    discord_file = discord.File(fp=log_chunk, filename="log_%s_part%d.txt" % (log['name'], part_counter))
                    await message.channel.send(content="Part %d of your log" % (part_counter), file=discord_file)

                    part_counter += 1

                await message.channel.send("Those were all the parts.")
            except MemoryError:
                await message.channel.send("Something went wrong. The developer has been notified.")
                await self._dev_message("fatal error", "Ran out of memory! While executing command \"%s\"" % (message.clean_content))

            await status_message.delete()
            
            log_virtual_file.close()
        
        return
        
        seconds = 0
        chunk_num = 0
        for output_chunk in self._slice_output(output_raw):
            seconds += 60
            await message.author.send(embed=discord.Embed(description=output_chunk), delete_after=seconds)
            chunk_num += 1
            
            #if chunk_num > 2 and not self._user_is_staff(message.author):
                #await message.author.send(embed=discord.Embed(description="You are not a staff member and therefore are not allowed to view past 3 chunks of a log."))
                #return
        
        await message.delete()
        await message.author.send(embed=discord.Embed(description="Log fully sent."))
        
        return

    async def _dev_cmd_move(self, message):
        """Work-in-progress version, to ensure the main version remains usable during development."""

        if not message.channel_mentions:
            await message.channel.send("Please specify a channel to move to.")
            return

        if not self._user_is_staff(message.author):
            await message.channel.send("Only staff is allowed to use this command.")
            return

        # Determine the source channel (where we get sent from) and the target channel (where we get sent to)
        target_chan = message.channel_mentions[0]
        src_chan = message.channel

        # Create the target endpoint of the channel link
        target_embed = discord.Embed(
            title='Channel Link',
            description="Conversation moved from <#%s> to <#%s>" % (src_chan.id, target_chan.id),
            color=self._data['embed_colour']
        )
        target_msg = await target_chan.send(embed=target_embed)

        # Create the source endpoint of the channel link
        #jump_url_target = "http://discordapp.com/channels/%s/%s/%s" % (target_chan.guild.id, target_chan.id, target_msg.id)
        src_msg = await src_chan.send(embed=discord.Embed(title='Channel Link', color=self._data['embed_colour'], description="A member of staff has requested that you move your conversation elsewhere.\n\n[Please click or tap here to move.](<%s>)" % (target_chan.jump_url)))

        # Now create the second link, that points back to the source endpoint, and add it to the target endpoint.
        jump_url_src = "http://discordapp.com/channels/%s/%s/%s" % (src_chan.guild.id, src_chan.id, src_msg.id)
        target_embed.description += "\n\n[Click here to go to the point where the conversation was moved.](<%s>)" % (src_chan.jump_url)
        await target_msg.edit(embed=target_embed)

        await self._dev_message('channel_link', "Someone moved a discussion to another channel.", channel=message.channel, public=False)

        return
    
    async def _cmd_wipe_messages(self, message, amt_to_wipe):
        if not self._user_is_staff(message.author) and not self._user_is_dev(message.author):
            await message.channel.send("You need to be staff to use this command.")
            return
        
        loading_msg = await message.channel.send('Wiping ChanLink messages from the channel..')
        
        if amt_to_wipe == "all":
            amt_to_wipe = False
        
        if amt_to_wipe:
            amt_to_wipe = int(amt_to_wipe)
            amt_to_wipe += 2
        
        amt_wiped = 1
        stop_wiping = False
        async for target_message in message.channel.history(limit=99999999):            
            if target_message.author.id == self.user.id:
                await target_message.delete()
                amt_wiped += 1
            elif target_message.author.name == self.user.name:
                await target_message.delete()
                amt_wiped += 1
            elif target_message.content.lower().startswith('cl!'):
                await target_message.delete()
            else:
                continue
            
            if amt_to_wipe and amt_wiped >= int(amt_to_wipe):
                break
                
            try:
                await self.wait_for('raw_message_deleted', timeout=0.5)
            except:
                pass
    
        if not amt_to_wipe:
            await message.channel.send("All ChanLink messages wiped from the channel.", delete_after=2)
        else:
            await message.channel.send("%d ChanLink messages wiped from the channel." % (int(amt_wiped-2)), delete_after=2)
                
        return
    

bot = ChanLinkBot()
bot.loop.create_task(bot.pop_channel_activity_tracker())
bot.run(TOKEN)
