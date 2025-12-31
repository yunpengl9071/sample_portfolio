-- Gensokyo Chronicles: Scarlet Moon Incident
-- A Touhou-style bullet hell shooter
-- Built with LÖVE 11.4+

function love.load()
    -- Set up window
    love.window.setTitle("Gensokyo Chronicles: Scarlet Moon Incident")
    love.window.setMode(800, 600, {resizable=false, vsync=true})

    -- Initialize random seed
    math.randomseed(os.time())

    -- Load game modules
    require('src/utils')
    require('src/player')
    require('src/bullet')
    require('src/enemy')
    require('src/boss')
    require('src/collision')
    require('src/ui')
    require('src/stage')
    require('src/dialogue')
    require('src/particles')

    -- Game state
    gameState = {
        current = "menu", -- menu, gameplay, dialogue, gameover, victory
        score = 0,
        continues = 3,
        difficulty = "Normal"
    }

    -- Initialize systems
    Bullets.init()
    Enemies.init()
    Bosses.init()
    Particles.init()
    UI.init()
    Stages.init()
    Dialogue.init()

    -- Game field boundaries
    GAME_LEFT = 50
    GAME_RIGHT = 450
    GAME_TOP = 50
    GAME_BOTTOM = 550
    GAME_WIDTH = GAME_RIGHT - GAME_LEFT
    GAME_HEIGHT = GAME_BOTTOM - GAME_TOP
end

function love.update(dt)
    if gameState.current == "menu" then
        updateMenu(dt)
    elseif gameState.current == "gameplay" then
        Player.update(dt)
        Bullets.update(dt)
        Enemies.update(dt)
        Bosses.update(dt)
        Particles.update(dt)
        Stages.update(dt)
        Collision.check()
    elseif gameState.current == "dialogue" then
        Dialogue.update(dt)
    elseif gameState.current == "gameover" then
        updateGameOver(dt)
    elseif gameState.current == "victory" then
        updateVictory(dt)
    end
end

function love.draw()
    if gameState.current == "menu" then
        drawMenu()
    elseif gameState.current == "gameplay" then
        drawGameplay()
    elseif gameState.current == "dialogue" then
        Dialogue.draw()
    elseif gameState.current == "gameover" then
        drawGameOver()
    elseif gameState.current == "victory" then
        drawVictory()
    end
end

function drawGameplay()
    -- Draw game field background
    love.graphics.setColor(0.05, 0.05, 0.15)
    love.graphics.rectangle('fill', GAME_LEFT, GAME_TOP, GAME_WIDTH, GAME_HEIGHT)

    -- Draw game field border
    love.graphics.setColor(1, 1, 1)
    love.graphics.setLineWidth(2)
    love.graphics.rectangle('line', GAME_LEFT, GAME_TOP, GAME_WIDTH, GAME_HEIGHT)

    -- Draw game elements
    Particles.draw()
    Enemies.draw()
    Bosses.draw()
    Bullets.draw()
    Player.draw()
    UI.draw()
end

function drawMenu()
    love.graphics.setColor(0.1, 0.05, 0.2)
    love.graphics.rectangle('fill', 0, 0, 800, 600)

    love.graphics.setColor(1, 0.9, 0.9)
    love.graphics.printf("Gensokyo Chronicles", 0, 100, 800, 'center')
    love.graphics.printf("Scarlet Moon Incident", 0, 140, 800, 'center')

    love.graphics.setColor(1, 1, 1)
    love.graphics.printf("Press Z to Start", 0, 300, 800, 'center')
    love.graphics.printf("Press X to Select Character", 0, 340, 800, 'center')
    love.graphics.printf("Current: " .. (Player.character or "Reimu"), 0, 380, 800, 'center')

    love.graphics.printf("Controls:", 0, 450, 800, 'center')
    love.graphics.printf("Arrow Keys: Move | Z: Shoot | X: Bomb | Shift: Focus", 0, 480, 800, 'center')
end

function drawGameOver()
    love.graphics.setColor(0.2, 0, 0)
    love.graphics.rectangle('fill', 0, 0, 800, 600)

    love.graphics.setColor(1, 0.3, 0.3)
    love.graphics.printf("Game Over", 0, 250, 800, 'center')
    love.graphics.setColor(1, 1, 1)
    love.graphics.printf("Score: " .. gameState.score, 0, 300, 800, 'center')
    love.graphics.printf("Press Z to Return to Menu", 0, 350, 800, 'center')
end

function drawVictory()
    love.graphics.setColor(0.1, 0.2, 0.3)
    love.graphics.rectangle('fill', 0, 0, 800, 600)

    love.graphics.setColor(1, 1, 0.5)
    love.graphics.printf("Victory!", 0, 200, 800, 'center')
    love.graphics.setColor(1, 1, 1)
    love.graphics.printf("Final Score: " .. gameState.score, 0, 250, 800, 'center')
    love.graphics.printf("You have saved Gensokyo!", 0, 300, 800, 'center')
    love.graphics.printf("Press Z to Return to Menu", 0, 400, 800, 'center')
end

function updateMenu(dt)
end

function updateGameOver(dt)
end

function updateVictory(dt)
end

function love.keypressed(key)
    if gameState.current == "menu" then
        if key == "z" then
            startGame()
        elseif key == "x" then
            toggleCharacter()
        end
    elseif gameState.current == "gameplay" then
        if key == "escape" then
            gameState.current = "menu"
        end
    elseif gameState.current == "dialogue" then
        Dialogue.keypressed(key)
    elseif gameState.current == "gameover" or gameState.current == "victory" then
        if key == "z" then
            gameState.current = "menu"
            gameState.score = 0
        end
    end
end

function startGame()
    Player.init()
    Bullets.clear()
    Enemies.clear()
    Bosses.clear()
    Particles.clear()
    gameState.score = 0
    Stages.start()
    gameState.current = "gameplay"
end

function toggleCharacter()
    if not Player.character or Player.character == "Reimu" then
        Player.character = "Marisa"
    else
        Player.character = "Reimu"
    end
end
