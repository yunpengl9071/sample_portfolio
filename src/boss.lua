-- Boss system with 6 unique bosses

Bosses = {
    current = nil,
    queue = {},
    currentIndex = 0,
    spellCardActive = false,
    spellCardTimer = 0,
    patternTimer = 0
}

-- Define all 6 bosses
local bossData = {
    {
        name = "Rumia",
        title = "Youkai of Dusk",
        health = 800,
        radius = 15,
        color = {0.8, 0.6, 0.2},
        score = 5000,
        spellCards = {
            {name = "Night Sign: Night Bird", duration = 30, pattern = "nightBird"},
            {name = "Darkness Sign: Demarcation", duration = 35, pattern = "demarcation"}
        },
        dialogue = {
            intro = "So you've come to stop the Scarlet Moon? How amusing!",
            defeat = "Ugh... I'll remember this..."
        }
    },
    {
        name = "Cirno",
        title = "Ice Fairy of the Lake",
        health = 1000,
        radius = 15,
        color = {0.3, 0.6, 1},
        score = 6000,
        spellCards = {
            {name = "Ice Sign: Icicle Fall", duration = 30, pattern = "icicleFall"},
            {name = "Freeze Sign: Perfect Freeze", duration = 35, pattern = "perfectFreeze"}
        },
        dialogue = {
            intro = "I'm the strongest! Prepare to be frozen!",
            defeat = "How could I lose? I'm supposed to be the strongest..."
        }
    },
    {
        name = "Meiling",
        title = "Colorful Rainbow Gatekeeper",
        health = 1200,
        radius = 16,
        color = {0.3, 1, 0.3},
        score = 7000,
        spellCards = {
            {name = "Rainbow Sign: Colorful Light Chaos", duration = 32, pattern = "colorfulChaos"},
            {name = "Extreme Color: Colorful Wind Chime", duration = 38, pattern = "windChime"}
        },
        dialogue = {
            intro = "None shall pass the gates of the Scarlet Devil Mansion!",
            defeat = "I've failed in my duty..."
        }
    },
    {
        name = "Patchouli",
        title = "Unmoving Great Library",
        health = 1500,
        radius = 16,
        color = {0.8, 0.5, 1},
        score = 8000,
        spellCards = {
            {name = "Fire Water Wood Metal Earth Sign", duration = 35, pattern = "fiveElements"},
            {name = "Royal Flare", duration = 40, pattern = "royalFlare"}
        },
        dialogue = {
            intro = "*cough* You've disturbed my research... Unforgivable.",
            defeat = "My magical theories... were they insufficient?"
        }
    },
    {
        name = "Sakuya",
        title = "Perfect and Elegant Maid",
        health = 1800,
        radius = 14,
        color = {0.7, 0.7, 1},
        score = 9000,
        spellCards = {
            {name = "Illusion Sign: Killing Doll", duration = 35, pattern = "killingDoll"},
            {name = "Time Sign: Private Square", duration = 42, pattern = "privateSquare"}
        },
        dialogue = {
            intro = "My mistress does not wish to be disturbed. Begone.",
            defeat = "Impressive... but my mistress still awaits."
        }
    },
    {
        name = "Remilia",
        title = "Scarlet Devil",
        health = 2500,
        radius = 18,
        color = {1, 0.3, 0.3},
        score = 15000,
        spellCards = {
            {name = "Scarlet Sign: Scarlet Shoot", duration = 38, pattern = "scarletShoot"},
            {name = "Scarlet Devil: Scarlet Gensokyo", duration = 45, pattern = "scarletGensokyo"},
            {name = "Forbidden Barrage: Starbow Break", duration = 50, pattern = "starbowBreak"}
        },
        dialogue = {
            intro = "Welcome to my domain. The Scarlet Moon shall consume Gensokyo!",
            defeat = "You... you've actually defeated me? No matter, this was merely a diversion..."
        }
    }
}

function Bosses.init()
    Bosses.current = nil
    Bosses.queue = {}
    Bosses.currentIndex = 0
    Bosses.spellCardActive = false
end

function Bosses.startBoss(index)
    if index < 1 or index > #bossData then return end

    local data = bossData[index]
    Bosses.current = {
        name = data.name,
        title = data.title,
        health = data.health,
        maxHealth = data.health,
        radius = data.radius,
        color = data.color,
        score = data.score,
        x = (GAME_LEFT + GAME_RIGHT) / 2,
        y = GAME_TOP + 80,
        vx = 0,
        vy = 0,
        spellCards = data.spellCards,
        currentSpellCard = 0,
        defeated = false,
        lifetime = 0,
        moveTimer = 0,
        dialogue = data.dialogue,
        targetX = (GAME_LEFT + GAME_RIGHT) / 2,
        targetY = GAME_TOP + 80
    }

    Bosses.currentIndex = index
    Bosses.spellCardActive = false
    Bosses.startNextSpellCard()
end

function Bosses.startNextSpellCard()
    if not Bosses.current then return end

    Bosses.current.currentSpellCard = Bosses.current.currentSpellCard + 1

    if Bosses.current.currentSpellCard > #Bosses.current.spellCards then
        Bosses.defeatCurrent()
        return
    end

    local spellCard = Bosses.current.spellCards[Bosses.current.currentSpellCard]
    Bosses.spellCardActive = true
    Bosses.spellCardTimer = spellCard.duration
    Bosses.patternTimer = 0

    -- Clear bullets when starting new spell card
    Bullets.clearEnemyBullets()
end

function Bosses.update(dt)
    if not Bosses.current or Bosses.current.defeated then return end

    local boss = Bosses.current
    boss.lifetime = boss.lifetime + dt
    boss.moveTimer = boss.moveTimer + dt

    -- Boss movement
    if boss.moveTimer > 3 then
        boss.targetX = GAME_LEFT + 50 + math.random() * (GAME_WIDTH - 100)
        boss.targetY = GAME_TOP + 50 + math.random() * 80
        boss.moveTimer = 0
    end

    boss.x = lerp(boss.x, boss.targetX, dt * 2)
    boss.y = lerp(boss.y, boss.targetY, dt * 2)

    -- Spell card
    if Bosses.spellCardActive then
        Bosses.spellCardTimer = Bosses.spellCardTimer - dt
        Bosses.patternTimer = Bosses.patternTimer + dt

        if Bosses.spellCardTimer <= 0 then
            Bosses.startNextSpellCard()
            return
        end

        -- Execute spell card pattern
        local spellCard = boss.spellCards[boss.currentSpellCard]
        Bosses.executePattern(spellCard.pattern, boss, dt)
    end
end

function Bosses.executePattern(pattern, boss, dt)
    local t = boss.lifetime

    if pattern == "nightBird" then
        if Bosses.patternTimer % 0.5 < dt then
            Bullets.patterns.spiral(boss.x, boss.y, 8, 100, t * 2, {0.8, 0.6, 0.2}, "circle")
        end
    elseif pattern == "demarcation" then
        if Bosses.patternTimer % 0.3 < dt then
            Bullets.patterns.circle(boss.x, boss.y, 16, 120, {0.2, 0.2, 0.2})
        end
    elseif pattern == "icicleFall" then
        if Bosses.patternTimer % 0.4 < dt then
            for i = 0, 5 do
                local x = GAME_LEFT + (GAME_WIDTH / 6) * (i + 0.5)
                Bullets.addEnemyBullet(x, GAME_TOP, 0, 150, "kunai", {0.5, 0.8, 1})
            end
        end
    elseif pattern == "perfectFreeze" then
        if Bosses.patternTimer % 0.6 < dt then
            Bullets.patterns.circle(boss.x, boss.y, 24, 80, {0.3, 0.6, 1})
            Bullets.patterns.circle(boss.x, boss.y, 24, 120, {0.6, 0.8, 1})
        end
    elseif pattern == "colorfulChaos" then
        if Bosses.patternTimer % 0.2 < dt then
            local colors = {{1, 0, 0}, {0, 1, 0}, {0, 0, 1}, {1, 1, 0}, {1, 0, 1}}
            local color = colors[math.floor(t * 5) % #colors + 1]
            Bullets.patterns.aimed(boss.x, boss.y, Player.x, Player.y, 5, 140, 0.3, color, "star")
        end
    elseif pattern == "windChime" then
        if Bosses.patternTimer % 0.5 < dt then
            for angle = 0, math.pi * 2, math.pi / 4 do
                Bullets.patterns.wave(boss.x, boss.y, 8, 100, angle, 10, {0.3, 1, 0.3})
            end
        end
    elseif pattern == "fiveElements" then
        if Bosses.patternTimer % 0.8 < dt then
            local elements = {
                {color = {1, 0.3, 0}, type = "star"},
                {color = {0.3, 0.3, 1}, type = "circle"},
                {color = {0.3, 1, 0.3}, type = "rice"},
                {color = {0.8, 0.8, 0.8}, type = "kunai"},
                {color = {0.6, 0.4, 0.2}, type = "circle"}
            }
            local elem = elements[(math.floor(Bosses.patternTimer / 0.8) % 5) + 1]
            Bullets.patterns.circle(boss.x, boss.y, 20, 100, elem.color)
        end
    elseif pattern == "royalFlare" then
        if Bosses.patternTimer % 0.3 < dt then
            Bullets.patterns.spiral(boss.x, boss.y, 10, 130, t * 3, {1, 0.5, 0.8}, "star")
            Bullets.patterns.spiral(boss.x, boss.y, 10, 130, -t * 3, {0.8, 0.3, 1}, "star")
        end
    elseif pattern == "killingDoll" then
        if Bosses.patternTimer % 0.25 < dt then
            Bullets.patterns.aimed(boss.x, boss.y, Player.x, Player.y, 9, 160, 0.15, {0.7, 0.7, 1}, "kunai")
        end
    elseif pattern == "privateSquare" then
        if Bosses.patternTimer % 0.4 < dt then
            for i = 0, 3 do
                local angle = (i / 4) * math.pi * 2 + t
                Bullets.patterns.circle(boss.x + math.cos(angle) * 80, boss.y + math.sin(angle) * 80, 12, 90, {0.5, 0.5, 1})
            end
        end
    elseif pattern == "scarletShoot" then
        if Bosses.patternTimer % 0.2 < dt then
            Bullets.patterns.aimed(boss.x, boss.y, Player.x, Player.y, 7, 180, 0.2, {1, 0.2, 0.2}, "rice")
        end
    elseif pattern == "scarletGensokyo" then
        if Bosses.patternTimer % 0.35 < dt then
            Bullets.patterns.circle(boss.x, boss.y, 32, 110, {1, 0, 0})
            Bullets.patterns.spiral(boss.x, boss.y, 16, 140, t * 4, {1, 0.3, 0.3}, "star")
        end
    elseif pattern == "starbowBreak" then
        if Bosses.patternTimer % 0.5 < dt then
            for i = 0, 6 do
                local angle = (i / 7) * math.pi * 2 + t * 0.5
                for j = 1, 5 do
                    local speed = 60 + j * 25
                    local vx = math.cos(angle) * speed
                    local vy = math.sin(angle) * speed
                    local hue = (i / 7 + j / 10) % 1
                    local color = hsvToRgb(hue, 1, 1)
                    Bullets.addEnemyBullet(boss.x, boss.y, vx, vy, "star", color)
                end
            end
        end
    end
end

function Bosses.draw()
    if not Bosses.current or Bosses.current.defeated then return end

    local boss = Bosses.current

    -- Draw boss aura
    love.graphics.setColor(boss.color[1], boss.color[2], boss.color[3], 0.3)
    love.graphics.circle('fill', boss.x, boss.y, boss.radius + 10 + math.sin(boss.lifetime * 3) * 3)

    -- Draw boss
    setColor(boss.color)
    love.graphics.circle('fill', boss.x, boss.y, boss.radius)

    -- Draw boss outline
    love.graphics.setColor(1, 1, 1)
    love.graphics.setLineWidth(2)
    love.graphics.circle('line', boss.x, boss.y, boss.radius)

    -- Draw boss health bar
    local barWidth = 300
    local barHeight = 20
    local barX = (800 - barWidth) / 2
    local barY = 20

    love.graphics.setColor(0, 0, 0, 0.7)
    love.graphics.rectangle('fill', barX, barY, barWidth, barHeight)

    love.graphics.setColor(1, 0.2, 0.2)
    local healthPercent = boss.health / boss.maxHealth
    love.graphics.rectangle('fill', barX, barY, barWidth * healthPercent, barHeight)

    love.graphics.setColor(1, 1, 1)
    love.graphics.setLineWidth(2)
    love.graphics.rectangle('line', barX, barY, barWidth, barHeight)

    -- Draw boss name
    love.graphics.setColor(1, 1, 1)
    love.graphics.print(boss.name .. " - " .. boss.title, barX, barY - 20)

    -- Draw spell card name
    if Bosses.spellCardActive and boss.currentSpellCard <= #boss.spellCards then
        local spellCard = boss.spellCards[boss.currentSpellCard]
        love.graphics.setColor(1, 1, 0.5)
        love.graphics.print(spellCard.name, barX, barY + barHeight + 5)

        -- Spell card timer
        love.graphics.print(string.format("%.1f", Bosses.spellCardTimer), barX + barWidth - 40, barY + barHeight + 5)
    end
end

function Bosses.defeatCurrent()
    if not Bosses.current then return end

    Bosses.current.defeated = true
    gameState.score = gameState.score + Bosses.current.score
    Bullets.clearEnemyBullets()

    -- Create victory particles
    for i = 1, 50 do
        local angle = math.random() * math.pi * 2
        local speed = 50 + math.random() * 150
        Particles.add(Bosses.current.x, Bosses.current.y, math.cos(angle) * speed, math.sin(angle) * speed, Bosses.current.color, 1)
    end

    -- Show defeat dialogue then move to next stage
    Dialogue.show(Bosses.current.name, Bosses.current.dialogue.defeat, function()
        Bosses.current = nil
        Stages.nextStage()
    end)
end

function hsvToRgb(h, s, v)
    local r, g, b
    local i = math.floor(h * 6)
    local f = h * 6 - i
    local p = v * (1 - s)
    local q = v * (1 - f * s)
    local t = v * (1 - (1 - f) * s)
    i = i % 6

    if i == 0 then r, g, b = v, t, p
    elseif i == 1 then r, g, b = q, v, p
    elseif i == 2 then r, g, b = p, v, t
    elseif i == 3 then r, g, b = p, q, v
    elseif i == 4 then r, g, b = t, p, v
    elseif i == 5 then r, g, b = v, p, q
    end

    return {r, g, b}
end
