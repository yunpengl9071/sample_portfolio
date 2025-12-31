-- Stage management system

Stages = {
    currentStage = 1,
    stageTime = 0,
    totalStages = 6,
    inBossFight = false,
    enemyWavesComplete = false
}

function Stages.init()
    Stages.currentStage = 1
    Stages.stageTime = 0
    Stages.inBossFight = false
    Stages.enemyWavesComplete = false
end

function Stages.start()
    Stages.currentStage = 1
    Stages.stageTime = 0
    Stages.inBossFight = false
    Stages.enemyWavesComplete = false
    Stages.startStage(1)
end

function Stages.startStage(num)
    Stages.currentStage = num
    Stages.stageTime = 0
    Stages.inBossFight = false
    Stages.enemyWavesComplete = false

    Enemies.clear()
    Bullets.clearEnemyBullets()

    if num > Stages.totalStages then
        gameState.current = "victory"
        return
    end

    -- Show stage intro dialogue
    local stageIntros = {
        {speaker = "Reimu/Marisa", text = "The Scarlet Moon has appeared over Gensokyo... I must investigate!"},
        {speaker = "Reimu/Marisa", text = "These fairies are getting stronger... Something is definitely wrong."},
        {speaker = "Reimu/Marisa", text = "The gate to the Scarlet Devil Mansion... I must get through!"},
        {speaker = "Reimu/Marisa", text = "Inside the mansion... The magical energy here is intense."},
        {speaker = "Reimu/Marisa", text = "I can sense a powerful presence ahead..."},
        {speaker = "Reimu/Marisa", text = "The Scarlet Devil herself! This ends now!"}
    }

    local intro = stageIntros[num]
    if intro then
        Dialogue.show(Player.character == "Reimu" and "Reimu Hakurei" or "Marisa Kirisame", intro.text, function()
            -- Callback after dialogue
        end)
    end
end

function Stages.update(dt)
    if Stages.inBossFight then
        -- Boss fight active
        if not Bosses.current or Bosses.current.defeated then
            Stages.inBossFight = false
        end
        return
    end

    Stages.stageTime = Stages.stageTime + dt

    -- Spawn enemies based on stage and time
    if not Stages.enemyWavesComplete then
        Stages.spawnEnemies(dt)
    end

    -- Check if wave complete and start boss
    if Stages.enemyWavesComplete and #Enemies.list == 0 and not Stages.inBossFight then
        Stages.startBossFight()
    end
end

function Stages.spawnEnemies(dt)
    local stage = Stages.currentStage
    local time = Stages.stageTime

    -- Stage 1: Rumia
    if stage == 1 then
        if time > 2 and time < 30 and time % 1.5 < dt then
            local x = GAME_LEFT + math.random() * GAME_WIDTH
            Enemies.spawn("fairy", x, GAME_TOP - 10)
        end
        if time > 35 and time < 55 and time % 2 < dt then
            local x = GAME_LEFT + math.random() * GAME_WIDTH
            Enemies.spawn("fairy_strong", x, GAME_TOP - 10)
        end
        if time > 60 then
            Stages.enemyWavesComplete = true
        end
    -- Stage 2: Cirno
    elseif stage == 2 then
        if time > 2 and time < 35 and time % 1.2 < dt then
            local x = GAME_LEFT + math.random() * GAME_WIDTH
            Enemies.spawn(math.random() > 0.5 and "fairy" or "fairy_strong", x, GAME_TOP - 10)
        end
        if time > 40 and time < 60 and time % 1.8 < dt then
            local x = GAME_LEFT + math.random() * GAME_WIDTH
            Enemies.spawn("ghost", x, GAME_TOP - 10)
        end
        if time > 65 then
            Stages.enemyWavesComplete = true
        end
    -- Stage 3: Meiling
    elseif stage == 3 then
        if time > 2 and time < 40 and time % 1 < dt then
            local x = GAME_LEFT + (time % 2 < 1 and 50 or GAME_WIDTH - 50)
            Enemies.spawn("fairy_strong", x, GAME_TOP - 10)
        end
        if time > 45 and time < 65 and time % 1.5 < dt then
            local x = GAME_LEFT + math.random() * GAME_WIDTH
            Enemies.spawn("youkai", x, GAME_TOP - 10)
        end
        if time > 70 then
            Stages.enemyWavesComplete = true
        end
    -- Stage 4: Patchouli
    elseif stage == 4 then
        if time > 2 and time < 45 and time % 1.3 < dt then
            local x = GAME_LEFT + math.random() * GAME_WIDTH
            local type = ({"ghost", "youkai", "fairy_strong"})[math.random(1, 3)]
            Enemies.spawn(type, x, GAME_TOP - 10)
        end
        if time > 50 and time < 70 and time % 0.8 < dt then
            local x = GAME_LEFT + math.random() * GAME_WIDTH
            Enemies.spawn("youkai", x, GAME_TOP - 10)
        end
        if time > 75 then
            Stages.enemyWavesComplete = true
        end
    -- Stage 5: Sakuya
    elseif stage == 5 then
        if time > 2 and time < 50 and time % 1 < dt then
            local x = GAME_LEFT + math.random() * GAME_WIDTH
            local type = ({"ghost", "youkai"})[math.random(1, 2)]
            Enemies.spawn(type, x, GAME_TOP - 10)
        end
        if time > 55 and time < 75 and time % 0.6 < dt then
            local x = GAME_LEFT + math.random() * GAME_WIDTH
            Enemies.spawn("youkai", x, GAME_TOP - 10)
        end
        if time > 80 then
            Stages.enemyWavesComplete = true
        end
    -- Stage 6: Remilia (Final Boss)
    elseif stage == 6 then
        if time > 2 and time < 60 and time % 0.8 < dt then
            local x = GAME_LEFT + math.random() * GAME_WIDTH
            local type = ({"ghost", "youkai", "fairy_strong"})[math.random(1, 3)]
            Enemies.spawn(type, x, GAME_TOP - 10)
        end
        if time > 65 and time < 90 and time % 0.5 < dt then
            local x = GAME_LEFT + math.random() * GAME_WIDTH
            Enemies.spawn("youkai", x, GAME_TOP - 10)
        end
        if time > 95 then
            Stages.enemyWavesComplete = true
        end
    end
end

function Stages.startBossFight()
    Stages.inBossFight = true
    local bossNames = {"Rumia", "Cirno", "Meiling", "Patchouli", "Sakuya", "Remilia"}

    -- Show boss intro dialogue
    Bosses.startBoss(Stages.currentStage)

    if Bosses.current then
        Dialogue.show(Bosses.current.name, Bosses.current.dialogue.intro, function()
            -- Start boss fight after dialogue
        end)
    end
end

function Stages.nextStage()
    if Stages.currentStage >= Stages.totalStages then
        gameState.current = "victory"
    else
        Stages.startStage(Stages.currentStage + 1)
    end
end
