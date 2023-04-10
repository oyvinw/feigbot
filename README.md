# feigbot
<img src="https://user-images.githubusercontent.com/25322338/231011599-2f1e40b1-68f7-4ae7-a408-eaee9660a822.png" width="250" />

- [feigbot](#feigbot)
  * [How to use](#how-to-use)
  * [Text Commands](#text-commands)
  * [Voice Commands](#voice-commands)
  * [Requirements](#requirements)

## How to use
This section is aimed at people wanting to interact with feigbot. If you want to know how to build and deploy your own feigbot, create an issue and we might include some better documentation.

### !reg - Become friends with feigbot
1. Go to: https://steamcommunity.com, log in, and press your profile picture at the top right of the page. Copy the url, it should look something like:
```
https://steamcommunity.com/id/{your-steam-name-or-id-here}
```
3. Go to https://steamid.xyz/ and paste in your url, press 'submit query'
4. Copy the value third from the top, labeled 'Steam32 ID'
5. Go to a Discord server where feigbot lives, and enter the command
```
!reg {your-Steam-32-ID}
```
6. Success! You can now use feigbot!

## Text Commands
### !blame - Find out who's to blame for your losses
![image](https://user-images.githubusercontent.com/25322338/231009225-9b67b61b-2554-4c1f-90ea-fee0d09cbecb.png)

### !sry - Apologize properly to your team for the loss
![image](https://user-images.githubusercontent.com/25322338/230563166-178cdc94-094c-4771-9ea4-ba65bf349098.png)

### !notsry - Salty justification for your loss
![image](https://user-images.githubusercontent.com/25322338/231008737-4332f543-0b80-4369-b8e9-ffa40b62e5ab.png)

### !anal - analysis (of course) of your previously played game
![image](https://user-images.githubusercontent.com/25322338/231013635-c2e4fba7-7b06-48f3-82a7-e2cd544bf54b.png)

### !analmatch {match_id} - analyse any game
![image](https://user-images.githubusercontent.com/25322338/231014398-4e4253e4-6a71-4a9c-a6a0-c786f9f96e9a.png)

### !tips - get some useful tips about the game you just played
![image](https://user-images.githubusercontent.com/25322338/231014493-fabb53dc-b763-40d4-8a1d-3dd371799f12.png)

## Voice Commands
Don't have time to read the chat? Feigbot will tell you all about it in voice chat as well. To do this, add
!{command} {language code} vc {optional name of a bot voice} (see all bot voices by doing the "!voices" command)

![image](https://user-images.githubusercontent.com/25322338/231010059-19362407-9a6d-4aea-9572-1dc1dbd70030.png)

![image](https://user-images.githubusercontent.com/25322338/231010087-b42a8e71-7ace-4405-a137-5fb48767f736.png)

There are also some special commands that work particularly well with voice commands
### !rap - Feigbot will do a sick rap about how you played like a god last game
### !vc-join - feigbot will join your voice channel
### !vc-kick - kick feigbot from whatever voice channel he's in :(
### !voices - get a list of all of feigbots possible voices

## Installation Requirements
[FFmpeg](https://ffmpeg.org/) \
[Opus Interactive Audio Codec](https://opus-codec.org/)
