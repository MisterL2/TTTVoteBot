# Created by MisterL2
import discord
import operator

f = open('token.txt','r')
TOKEN = f.read()
f.close()

client = discord.Client()


voteMasters = [] #Users
voters = [] #Users
victims = [] #Users

logChannels = {} #Server : Channel
serverHasVote = {} #Server: True/False
hasVoted = {} #User.name : True/False
voteCount = {} #User.name : int

activityBonus = {} #User.name : int

def user_react(reaction,user,modifier,votedPlayer):
    global voteCount
    global victims
    global voteMasters
    global activityBonus
    
    if user in voteMasters: #Special permissions for voteMasters
        activityEmojiList = ['\U0001F947','\U0001F948','\U0001F949','1\u20e3','2\u20e3','3\u20e3']
        if reaction.emoji in activityEmojiList:
            if modifier==-1: #activityEmoji was removed
                activityBonus[votedPlayer]=0
                otherReacts=0
                for otherReaction in reaction.message.reactions:
                    if otherReaction.emoji in activityEmojiList and otherReaction.count==2:
                        otherReacts+=1

                if otherReacts==0: #Resets to zero if no other activity reactions are selected
                    return 'ActivityBonus for player ' + votedPlayer + ' has been reset to 0.'
                elif otherReacts==1: #Resets to the other selected option, if exactly one other activity reaction is selected
                    if otherReaction.emoji == activityEmojiList[0]:
                        activityBonus[votedPlayer] = 1
                    elif otherReaction.emoji == activityEmojiList[1]:
                        activityBonus[votedPlayer] = 2
                    elif otherReaction.emoji == activityEmojiList[2]:
                        activityBonus[votedPlayer] = 3
                    elif otherReaction.emoji == activityEmojiList[3]:
                        activityBonus[votedPlayer] = -1
                    elif otherReaction.emoji == activityEmojiList[4]:
                        activityBonus[votedPlayer] = -2
                    elif otherReaction.emoji == activityEmojiList[5]:
                        activityBonus[votedPlayer] = -3
                    return 'ActivityBonus for player ' + votedPlayer + ' has been changed to ' + str(activityBonus[votedPlayer])
                else:
                    return 'ActivityBonus for player ' + votedPlayer + ' has been reset to 0.\nWARNING: You have multiple other emotes selected - the current ActivityBonus for that player is 0.'
                
                
            elif reaction.emoji == activityEmojiList[0]:
                activityBonus[votedPlayer] = 1
            elif reaction.emoji == activityEmojiList[1]:
                activityBonus[votedPlayer] = 2
            elif reaction.emoji == activityEmojiList[2]:
                activityBonus[votedPlayer] = 3
            elif reaction.emoji == activityEmojiList[3]:
                activityBonus[votedPlayer] = -1
            elif reaction.emoji == activityEmojiList[4]:
                activityBonus[votedPlayer] = -2
            elif reaction.emoji == activityEmojiList[5]:
                activityBonus[votedPlayer] = -3
                
            return 'ActivityBonus for player ' + votedPlayer + ' has been set to ' + str(activityBonus[votedPlayer])

            
    if user in victims and user.name == votedPlayer: #Voting on yourself -> Can be circumvented by discord rename
        if modifier==1:
            print(user.name + ' tried to vote on himself LUL')
            return 'You can\'t vote on yourself, tryhard!'
        else:
            print(user.name + ' removed the fake vote on himself LUL x2')
            return 'Yeah, you better remove that fraudulent vote'
        
    elif reaction.emoji == '✅' and reaction.message.content.startswith('-> ') and votedPlayer in [x.name for x in victims] and (reaction.count==2 or modifier==-1 and reaction.count==1): #Valid UPvote
        voteCount[votedPlayer]+=modifier #Automatically works in reverse, if the reaction was removed rather than added
        
    elif reaction.emoji == '❌' and reaction.message.content.startswith('-> ') and votedPlayer in [x.name for x in victims] and (reaction.count==2 or modifier==-1 and reaction.count==1): #Valid DOWNvote
        voteCount[votedPlayer]-=modifier
        
    else:
        print('Invalid reaction')
        return 'Invalid reaction'

    hasVoted[user.name]=True
    return 'Flawless'


def get_text_channels():
    lst = []
    for server in client.servers:
            for channel in server.channels:
                if channel.type == discord.ChannelType.text:
                    lst.append(str(server) + ": " + str(channel))
    return lst


def get_server_members(server,memberType):
    members = []
    for member in server.members:
        if memberType=='staff':
            for role in [x.name.lower() for x in member.roles]:
                if 'support' in role or 'moderator' in role or 'admin' in role or 'votemaster' in role or 'owner' in role:
                    members.append(member)
                    break

        elif memberType=='lowstaff':
            for role in [x.name.lower() for x in member.roles]:
                if 'admin' in role or 'scripter' in role or 'owner' in role:
                    break
                elif 'support' in role or 'moderator' in role: #VoteMaster not immune from being selected themselves as lowstaff
                    isLow=True
                    for role in [x.name.lower() for x in member.roles]: #Checks all the roles to see that they are not ADDITIONALLY admin
                        if 'admin' in role or 'scripter' in role:
                            isLow=False
                            break
                    if isLow:
                        members.append(member)
                    break
                    
        #elif memberType=='all': #Dangerous! Massive spam potential!
        #    members.append(member)
            
        elif memberType=='human' and not member.bot:
            members.append(member)

        elif memberType=='VoteMaster':
            for role in [x.name.lower() for x in member.roles]:
                if 'votemaster' in role and member not in members:
                    members.append(member)
                    
    return members


def vote_stats(detail):
    global voteCount
    global activityBonus
    totalVoteCount = {}
    for victim in voteCount.keys():
        totalVoteCount[victim]=voteCount[victim]
        if victim in activityBonus.keys(): #If there is a registered bonus
            totalVoteCount[victim]+=activityBonus[victim] #The bonus is only temporarily added
    
    sortedVotes = sorted(totalVoteCount.items(), key=operator.itemgetter(1), reverse=True)
    voteString = ""
    i=0
    for victim in sortedVotes:
        i+=1
        if detail:
            voteString+=str(i) + ". " + victim[0] + ": " + str(victim[1]) +  "\n"
        else:
            voteString+=str(i) + ". " + victim[0] + "\n"
            
    return voteString


@client.event
async def on_message(message):
    global victims
    global voteCount
    global voters
    global hasVoted
    global voteMasters
    
    if message.author == client.user and message.channel.type == discord.ChannelType.text: #Doesn't respond to its own messages in NON-PRIVATE channels
        #print("The bot doesn't respond to its own messages in non-private channels!")
        return

    if message.channel.type == discord.ChannelType.private: #Private message
        if message.author == client.user: #Reacting to its own message
            if message.content.startswith('-> '):
                await client.add_reaction(message,'✅') #Up-vote Emoji
                await client.add_reaction(message,'❌') #Down-vote Emoji
                if message.channel.user in voteMasters:
                    await client.add_reaction(message,'\U0001F947')
                    await client.add_reaction(message,'\U0001F948')
                    await client.add_reaction(message,'\U0001F949')
                    await client.add_reaction(message,'1\u20e3')
                    await client.add_reaction(message,'2\u20e3')
                    await client.add_reaction(message,'3\u20e3')
                
        elif message.author in voteMasters: #Reacting to a VoteMaster
            await client.send_message(message.author, 'I hail thee, great master!')
            if message.content.startswith('stats'):
                await client.send_message(message.author, vote_stats(True))

            elif message.content.startswith('amount'):
                total=0
                amount=0
                notVoted="The following users haven't voted yet: "
                for voter in hasVoted.keys():
                    if(hasVoted[voter]):
                        amount+=1
                    else:
                        notVoted+=voter + ", "
                    total+=1
                await client.send_message(message.author, '{} out of {} have voted!'.format(amount,total))
                await client.send_message(message.author, notVoted)



    #Anything from here on are NON-PRIVATE messages
                
    elif message.content.startswith('GANDALF'):
        print("Fröhlichen gandalf!")
        if message.author in voteMasters:
            if serverHasVote[message.server]:
                for VoteMaster in get_server_members(message.server,'VoteMaster'):
                    await client.send_message(VoteMaster, vote_stats(True))
                    
                serverHasVote[message.server]=False #No more vote in progress
                await client.send_message(message.channel, 'The vote has ended with the following results')
                await client.send_message(message.channel, vote_stats(False))
                    
                try:
                    await client.send_message(logChannels[message.server], vote_stats(True))
                except KeyError:
                    print("No log channel set - Cannot display results!")
            else:
                await client.send_message(message.channel, 'No Gandalf - Nobody trying to pass! (No vote on this server!)')    
        else:
            await client.send_message(message.channel, 'WHICH PUNY MORTAL CALLS ON THE NAME OF GANDALF?')

    elif message.content.startswith('setLogChannel'):
        if 'VoteMaster' not in [y.name for y in message.author.roles]:
            print('You ain\'t setting anything, m8')
            await client.send_message(message.channel, 'You ain\'t setting anything, m8')
        else:
            if message.server in logChannels.keys():
                await client.send_message(message.channel, 'Log channel changed (previously \'' + logChannels[message.server].name + '\')!')
            else:
                await client.send_message(message.channel, 'Log channel set!')
                
            logChannels[message.server]=message.channel #refers to global by default
    
    elif message.content.startswith('show all channels on this server'): #Fun TEST function
        for channel in channel.server.channels:
            await client.send_message(message.channel, channel)
    
    elif message.content.lower().startswith('show my permissions'):
        for permission in message.channel.permissions_for(message.author):
            await client.send_message(message.channel, permission)

    elif message.content.startswith('show my roles'):
        for role in message.author.roles[1:]: #avoid @everyone
            await client.send_message(message.channel, role)

    elif message.content.startswith('YOU SHALL NOT PASS'):
        if 'VoteMaster' not in [y.name for y in message.author.roles]:
            print("Insufficient permissions to stop anyone, fool!")
            await client.send_message(message.channel, 'Insufficient permissions to stop anyone, fool!')
        elif message.server in serverHasVote.keys() and serverHasVote[message.server]: #if voteStarted is TRUE
            print("There is already a vote in progress, idiot!")
            await client.send_message(message.channel, 'There is already a vote in progress, idiot!')
        else:
            print("Vote started")
            await client.send_message(message.channel, 'Vote started!')
            serverHasVote[message.server]=True #Adds channel to list if not already in there and sets voteStarted to TRUE
            voters = get_server_members(message.server,'staff') #refers to global by default
            victims = get_server_members(message.server,'lowstaff') #refers to global by default
            for voter in voters:
                hasVoted[voter.name]=False
            voteCount.clear() #if only working on one server
            
            for victim in victims:
                voteCount[victim.name]=0
                
            for VoteMaster in get_server_members(message.server,'VoteMaster'):
                voteMasters.append(VoteMaster) #List of VoteMaster IDs
             
            embed = discord.Embed(title="A wild vote appears", color=0x00ff00)
            blockers = []
            for voter in voters:
                try:
                    await client.send_message(voter, embed=embed)
                except Exception: #If some retard blocks the bot
                    try:
                        await client.send_message(logChannels[message.server], voter + " has blocked the bot!!!")
                        print(voter + " has blocked the bot!!!")
                    except Exception: #Shell unicode exception
                        print("Someone with an unprintable name has blocked the bot!!!")
                    continue #Does not attempt to send further messages for this player (who blocked the bot!)
                        
                for victim in victims:
                    if victim!=voter or voter in voteMasters: #Don't even give the chance to vote for yourself, unless you are votemaster and need to manage activitybonus (for which the self-vote protection in user_react needs to stay!)
                        await client.send_message(voter, '-> ' + victim.name)        
    else:
        pass
        #print("Unrecognised command!")


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    #print(client.user.id)
    print('------')


@client.event
async def on_reaction_add(reaction,user):
    if reaction.message.author==client.user and reaction.message.channel.type == discord.ChannelType.private and reaction.count==2: #Private channel, the message being reacted to is from the bot and the REACTION is NOT from the bot, as determined by reaction.count==2, so 2 people have reacted to it, hence both the bot and the user
        votedPlayer=reaction.message.content[3:]
        response=user_react(reaction,user,1,votedPlayer)
        if response=='Flawless' or response.startswith('ActivityBonus'): #Correct -> Logged
            if response.startswith('ActivityBonus'): #Send feedback to user anyways
                await client.send_message(user,response)
            for server in serverHasVote.keys():
                if serverHasVote[server]: #Vote is started on that server
                    if user in server.members: #The user is a member in a server that has a channel with an ongoing vote
                        try:
                            await client.send_message(logChannels[server], user.name + " has voted " + reaction.emoji + " on " + votedPlayer)
                        except KeyError:
                            print("No log channel is set, cannot save log!")
                            print(user.name + " has voted " + reaction.emoji + " on " + votedPlayer)
                        return
        else:
            await client.send_message(user,response)
            
@client.event
async def on_reaction_remove(reaction,user):
    if reaction.message.author==client.user and reaction.message.channel.type == discord.ChannelType.private: #Private channel, the message being reacted to is from the bot
        votedPlayer=reaction.message.content[3:]
        response=user_react(reaction,user,-1,votedPlayer)
        if response=='Flawless' or response.startswith('ActivityBonus'): #Correct -> Logged
            if response.startswith('ActivityBonus'): #Send feedback to user anyways
                await client.send_message(user,response)
            for server in serverHasVote.keys():
                if serverHasVote[server]: #Vote is started on that server
                    if user in server.members: #The user is a member in a server that has a channel with an ongoing vote
                        try:
                            await client.send_message(logChannels[server], user.name + " has removed his " + reaction.emoji + " on " + votedPlayer)
                        except KeyError:
                            print("No log channel is set, cannot save log!")
                            print(user.name + " has removed his " + reaction.emoji + " on " + votedPlayer)
                            return
        else:
            await client.send_message(user,response)



client.run(TOKEN)
