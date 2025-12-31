-- Dialogue system for storytelling

Dialogue = {
    active = false,
    speaker = "",
    text = "",
    callback = nil,
    displayedText = "",
    textTimer = 0,
    textSpeed = 0.03,
    complete = false
}

function Dialogue.init()
    Dialogue.active = false
end

function Dialogue.show(speaker, text, callback)
    Dialogue.active = true
    Dialogue.speaker = speaker
    Dialogue.text = text
    Dialogue.callback = callback
    Dialogue.displayedText = ""
    Dialogue.textTimer = 0
    Dialogue.complete = false

    -- Pause the game
    local prevState = gameState.current
    gameState.current = "dialogue"
    Dialogue.previousState = prevState
end

function Dialogue.update(dt)
    if not Dialogue.active then return end

    if not Dialogue.complete then
        Dialogue.textTimer = Dialogue.textTimer + dt

        if Dialogue.textTimer >= Dialogue.textSpeed then
            Dialogue.textTimer = 0
            local len = #Dialogue.displayedText
            if len < #Dialogue.text then
                Dialogue.displayedText = Dialogue.text:sub(1, len + 1)
            else
                Dialogue.complete = true
            end
        end
    end
end

function Dialogue.draw()
    if not Dialogue.active then return end

    -- Dim background
    love.graphics.setColor(0, 0, 0, 0.7)
    love.graphics.rectangle('fill', 0, 0, 800, 600)

    -- Dialogue box
    local boxX = 50
    local boxY = 400
    local boxWidth = 700
    local boxHeight = 150

    love.graphics.setColor(0.1, 0.1, 0.3, 0.9)
    love.graphics.rectangle('fill', boxX, boxY, boxWidth, boxHeight)

    love.graphics.setColor(1, 1, 1)
    love.graphics.setLineWidth(3)
    love.graphics.rectangle('line', boxX, boxY, boxWidth, boxHeight)

    -- Speaker name
    love.graphics.setColor(1, 1, 0.7)
    love.graphics.print(Dialogue.speaker, boxX + 20, boxY + 10)

    -- Dialogue text
    love.graphics.setColor(1, 1, 1)
    love.graphics.printf(Dialogue.displayedText, boxX + 20, boxY + 40, boxWidth - 40, 'left')

    -- Continue indicator
    if Dialogue.complete then
        love.graphics.setColor(1, 1, 1, 0.5 + math.sin(love.timer.getTime() * 5) * 0.5)
        love.graphics.print("Press Z to continue", boxX + boxWidth - 180, boxY + boxHeight - 30)
    end
end

function Dialogue.keypressed(key)
    if not Dialogue.active then return end

    if key == "z" then
        if Dialogue.complete then
            Dialogue.close()
        else
            -- Skip to end of text
            Dialogue.displayedText = Dialogue.text
            Dialogue.complete = true
        end
    end
end

function Dialogue.close()
    Dialogue.active = false

    if Dialogue.callback then
        Dialogue.callback()
    end

    gameState.current = Dialogue.previousState or "gameplay"
end
