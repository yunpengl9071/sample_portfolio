-- UI system

UI = {}

function UI.init()
end

function UI.draw()
    local uiX = 500
    local uiY = 100

    love.graphics.setColor(0.1, 0.1, 0.2, 0.8)
    love.graphics.rectangle('fill', uiX - 10, uiY - 10, 290, 400)

    love.graphics.setColor(1, 1, 1)
    love.graphics.setLineWidth(2)
    love.graphics.rectangle('line', uiX - 10, uiY - 10, 290, 400)

    -- Character info
    local charInfo = Player.getCharacterInfo()
    love.graphics.setColor(1, 1, 1)
    love.graphics.print("Character:", uiX, uiY)
    setColor(charInfo.color)
    love.graphics.print(charInfo.name, uiX, uiY + 20)
    love.graphics.setColor(0.8, 0.8, 0.8)
    love.graphics.print(charInfo.description, uiX, uiY + 40)

    -- Score
    love.graphics.setColor(1, 1, 1)
    love.graphics.print("Score:", uiX, uiY + 80)
    love.graphics.print(tostring(gameState.score), uiX, uiY + 100)

    -- Lives
    love.graphics.print("Lives:", uiX, uiY + 140)
    for i = 1, Player.lives do
        setColor(charInfo.color)
        love.graphics.circle('fill', uiX + (i - 1) * 25 + 10, uiY + 165, 8)
    end

    -- Bombs
    love.graphics.setColor(1, 1, 1)
    love.graphics.print("Bombs:", uiX, uiY + 190)
    for i = 1, Player.bombs do
        love.graphics.setColor(1, 1, 0.5)
        love.graphics.rectangle('fill', uiX + (i - 1) * 25 + 5, uiY + 210, 15, 15)
    end

    -- Power level
    love.graphics.setColor(1, 1, 1)
    love.graphics.print("Power:", uiX, uiY + 250)
    love.graphics.print(string.format("%.1f", Player.power), uiX, uiY + 270)

    -- Stage info
    love.graphics.print("Stage:", uiX, uiY + 310)
    love.graphics.print(tostring(Stages.currentStage), uiX, uiY + 330)

    -- FPS
    love.graphics.setColor(0.6, 0.6, 0.6)
    love.graphics.print("FPS: " .. tostring(love.timer.getFPS()), uiX, uiY + 360)
end
