# 🤖 TimbasBot - Automated In-House & Community Tournament Bot

## 📝 Overview

 TimbasBot is a Discord bot designed to revolutionize the custom game experience for smaller, private communities and groups of friends within League of Legends. Tired of manual team balancing, disorganized lobbies, and the lack of persistent stats for your in-house games? Our bot automates the entire process, making competitive custom games fun, fair, and engaging.

## ✨ Features

### Seamless Game Organization
The bot streamlines the pre-game setup, eliminating the hassle of manual coordination.
* **Automated Queue Management:** Players can easily join a queue within Discord using a simple command.
* **Intelligent Team Creation:** Once 10 players are in queue, the bot automatically generates balanced teams (initially randomized, with future plans for MMR-based balancing).
* **Voice Channel Automation:** Upon match start, players are automatically moved to private voice channels for their respective teams, ensuring clear communication and focus.

> ### Advanced Match Analytics (Pending Riot API Access)
With access to the Tournament API, we aim to transform casual custom games into a rich, data-driven competitive experience.
* **Automated Post-Game Data:** Automatically collects match results, player performance, and key game events.
* **Persistent Player Profiles:** Each player will have a profile, tracking their win/loss record, KDA, favorite champions, and more across all in-house games.
* **Private Community MMR System:** An internal MMR system, distinct from Riot's official ranked system, will be implemented to ensure balanced and fair matches for future team creations.
* **Dynamic Leaderboards:** See who's climbing the ranks! Track top players by wins, win rate, KDA, and even champion-specific performance.
* **Live Match Updates:** Real-time updates on ongoing matches within Discord, displaying scores, gold differences, and important objectives.

> ## 🎯 Our Goal & Vision

Our ultimate vision is to empower small communities and friend groups to create their own structured, engaging, and competitive environment for custom League of Legends games. By providing professional-grade tools typically reserved for larger tournaments, we aim to:
* Foster stronger friendships through organized play.
* Deepen long-term community engagement with League of Legends.
* Create a fun, fair, and continuously evolving competitive scene at the grassroots level.

This project will make "in-house" games not just easier to organize, but truly rewarding and memorable, giving every match a sense of purpose and progression.

## 🚀 How to Add TimbasBot to Your Server

Ready to elevate your in-house games?
1.  **[Click here to invite the bot to your server!]([...])**
2.  **[Join our support server for help and suggestions.]([...])**

## 🛠️ Development & API Usage (For Riot Games Developer Relations)

This section is for the Riot Games Developer Relations team, outlining our responsible API usage.

We are actively seeking a production key for the Riot Games Tournament API to unlock the full potential of this bot's analytics features. We have thoroughly reviewed the API documentation and tested the provided stubs.

**Key considerations for API usage:**
* **Single Tournament Provider:** Our system will operate under a single tournament provider and one long-running tournament ID per Discord server. All new match codes will be generated under this established tournament structure.
* **Rate Limit Adherence:** To ensure responsible and efficient use of the API, we will implement a server-side cooldown. A new match can only be created via the API after a 20-minute interval has passed since the previous one. This strategy is designed to minimize excessive API calls and ensure a stable and respectful integration with Riot's services.
* **Compliance:** We are committed to adhering to all Riot Games' Terms of Use and Legal Jibber Jabber, including policies against monetizing the app, creating official MMR alternatives (our system is private and internal only for balancing), and brand guidelines.

Our focus is purely on enhancing player experience in a non-disruptive, community-centric manner.

## 🤝 Contribution & Support

This project is currently developed and maintained by JuserDev. For feature requests or bug reports, please use the appropriate channels in our support server.

## 📞 Contact

For any inquiries or support, please join our **[Discord Support Server]([https://discord.gg/xN3xzTsUV7])** or contact us at **[gabrielrpg13@gmail.com]**.