# Gensokyo Chronicles: Scarlet Moon Incident

A Touhou Project-inspired bullet hell shooter built with LÖVE (Love2D) and Lua.

## Story

A mysterious Scarlet Moon has appeared over Gensokyo, threatening to consume the land in eternal darkness. As either the shrine maiden Reimu Hakurei or the magician Marisa Kirisame, you must investigate this incident and defeat the six powerful youkai behind this crisis!

### The Six Bosses

1. **Rumia** - Youkai of Dusk
   - First encounter in the darkening forest
   - Spell Cards: Night Bird, Demarcation

2. **Cirno** - Ice Fairy of the Lake
   - The self-proclaimed strongest blocks your path
   - Spell Cards: Icicle Fall, Perfect Freeze

3. **Hong Meiling** - Colorful Rainbow Gatekeeper
   - Guardian of the Scarlet Devil Mansion gates
   - Spell Cards: Colorful Light Chaos, Colorful Wind Chime

4. **Patchouli Knowledge** - Unmoving Great Library
   - The mansion's resident magician
   - Spell Cards: Fire Water Wood Metal Earth Sign, Royal Flare

5. **Sakuya Izayoi** - Perfect and Elegant Maid
   - Head maid with time manipulation powers
   - Spell Cards: Killing Doll, Private Square

6. **Remilia Scarlet** - The Scarlet Devil
   - Mistress of the mansion and mastermind behind the Scarlet Moon
   - Spell Cards: Scarlet Shoot, Scarlet Gensokyo, Starbow Break

## Features

- **Two Playable Characters**
  - **Reimu Hakurei**: Homing amulet shots, balanced playstyle
  - **Marisa Kirisame**: Powerful straight laser shots, high damage

- **6 Unique Boss Battles** with multiple spell card patterns
- **Authentic Touhou-style Gameplay**
  - Bullet hell danmaku patterns
  - Focused movement for precision dodging
  - Bomb system for emergency clearing
  - Lives and continues system

- **Rich Storyline** with character dialogue
- **Multiple Enemy Types** (Fairies, Ghosts, Youkai)
- **Beautiful Bullet Patterns** inspired by classic Touhou games

## Installation

### Requirements

- LÖVE (Love2D) 11.4 or higher
- Download from: https://love2d.org/

### Windows

1. Install LÖVE from the official website
2. Download/clone this repository
3. Drag the game folder onto `love.exe` OR
4. Run from command line: `love.exe path/to/game/folder`

### macOS

1. Install LÖVE from the official website
2. Download/clone this repository
3. Run from terminal:
   ```bash
   open -n -a love "path/to/game/folder"
   ```

### Linux

1. Install LÖVE through your package manager:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install love

   # Arch Linux
   sudo pacman -S love

   # Fedora
   sudo dnf install love
   ```

2. Run the game:
   ```bash
   love path/to/game/folder
   ```

## Controls

- **Arrow Keys**: Move your character
- **Z**: Shoot
- **X**: Bomb (clears bullets and damages enemies)
- **Shift**: Focus mode (slower movement, shows hitbox)
- **Escape**: Return to menu (during gameplay)

## How to Play

1. **Character Selection**: Press X at the menu to switch between Reimu and Marisa
2. **Movement**: Use arrow keys to move. Hold Shift for precise dodging
3. **Shooting**: Hold Z to fire continuously
4. **Bombs**: Press X to use a bomb when surrounded by bullets
5. **Hitbox**: While holding Shift, you can see your small hitbox - only this counts for collisions!
6. **Survival**: Avoid enemy bullets and defeat all 6 bosses to save Gensokyo

## Gameplay Tips

- **Focus on dodging** - Your hitbox is very small when in focus mode (Shift)
- **Learn boss patterns** - Each spell card has a specific pattern you can memorize
- **Use bombs wisely** - Bombs clear all bullets and make you invincible temporarily
- **Don't be greedy** - Surviving is more important than dealing damage
- **Character differences**:
  - Reimu's homing shots are better for beginners (easier to hit enemies)
  - Marisa's lasers deal more damage but require better aim

## Game Mechanics

### Lives and Continues
- Start with 3 lives
- Lose a life when hit by enemy bullets
- Game over when all lives are lost

### Power System
- Power level affects your shot strength
- Lose power when you die
- Starts at 1.0, maximum varies by character

### Spell Cards
- Each boss has multiple spell card attacks
- Defeat all spell cards to defeat the boss
- Each spell card has a time limit and unique pattern

### Scoring
- Defeat enemies: 50-300 points
- Defeat bosses: 5,000-15,000 points
- Higher scores for completing spell cards quickly

## Technical Details

### File Structure
```
/
├── main.lua                 # Main game entry point
├── src/
│   ├── utils.lua           # Utility functions
│   ├── player.lua          # Player system (Reimu/Marisa)
│   ├── bullet.lua          # Bullet system and patterns
│   ├── enemy.lua           # Enemy system
│   ├── boss.lua            # Boss system with 6 bosses
│   ├── collision.lua       # Collision detection
│   ├── ui.lua              # User interface
│   ├── stage.lua           # Stage progression
│   ├── dialogue.lua        # Dialogue system
│   └── particles.lua       # Visual effects
└── README.md
```

### Performance
- Optimized for 60 FPS gameplay
- Handles hundreds of bullets on screen
- Low memory footprint

## Credits

- **Game Design**: Inspired by Touhou Project by ZUN (Team Shanghai Alice)
- **Programming**: Built with LÖVE/Lua
- **Characters**: Reimu Hakurei, Marisa Kirisame, and bosses from Touhou Project

## License

This is a fan game inspired by Touhou Project. All characters and concepts belong to their respective owners (ZUN/Team Shanghai Alice). This game is free and not for commercial use.

## Acknowledgments

Special thanks to:
- ZUN for creating the incredible Touhou Project series
- The LÖVE community for the amazing game framework
- All Touhou fans who have kept the community vibrant

---

**Enjoy the game and good luck saving Gensokyo!** 🎮✨
