-- Player system with Reimu and Marisa

Player = {
    x = 0,
    y = 0,
    speed = 200,
    focusSpeed = 100,
    radius = 3,
    hitboxRadius = 2,
    lives = 3,
    bombs = 3,
    power = 1,
    invincible = false,
    invincibleTime = 0,
    shootCooldown = 0,
    character = "Reimu",
    bombActive = false,
    bombTime = 0,
    deathTime = 0,
    respawning = false
}

local characters = {
    Reimu = {
        name = "Reimu Hakurei",
        color = {1, 0.2, 0.2},
        shotType = "homing",
        shotSpeed = 400,
        shotDamage = 1,
        bombDuration = 3,
        description = "Homing amulets"
    },
    Marisa = {
        name = "Marisa Kirisame",
        color = {1, 1, 0.3},
        shotType = "laser",
        shotSpeed = 500,
        shotDamage = 1.5,
        bombDuration = 3,
        description = "Powerful lasers"
    }
}

function Player.init()
    Player.x = (GAME_LEFT + GAME_RIGHT) / 2
    Player.y = GAME_BOTTOM - 50
    Player.lives = 3
    Player.bombs = 3
    Player.power = 1
    Player.invincible = false
    Player.invincibleTime = 0
    Player.shootCooldown = 0
    Player.bombActive = false
    Player.bombTime = 0
    Player.deathTime = 0
    Player.respawning = false
    Player.character = Player.character or "Reimu"
end

function Player.update(dt)
    if Player.respawning then
        Player.deathTime = Player.deathTime + dt
        if Player.deathTime >= 2 then
            Player.respawning = false
            Player.invincible = true
            Player.invincibleTime = 3
        end
        return
    end

    -- Update invincibility
    if Player.invincible then
        Player.invincibleTime = Player.invincibleTime - dt
        if Player.invincibleTime <= 0 then
            Player.invincible = false
        end
    end

    -- Update bomb
    if Player.bombActive then
        Player.bombTime = Player.bombTime - dt
        if Player.bombTime <= 0 then
            Player.bombActive = false
        end
    end

    -- Movement
    local isFocused = love.keyboard.isDown('lshift') or love.keyboard.isDown('rshift')
    local moveSpeed = isFocused and Player.focusSpeed or Player.speed

    if love.keyboard.isDown('left') then
        Player.x = Player.x - moveSpeed * dt
    end
    if love.keyboard.isDown('right') then
        Player.x = Player.x + moveSpeed * dt
    end
    if love.keyboard.isDown('up') then
        Player.y = Player.y - moveSpeed * dt
    end
    if love.keyboard.isDown('down') then
        Player.y = Player.y + moveSpeed * dt
    end

    -- Clamp to game field
    Player.x = clamp(Player.x, GAME_LEFT + 10, GAME_RIGHT - 10)
    Player.y = clamp(Player.y, GAME_TOP + 10, GAME_BOTTOM - 10)

    -- Shooting
    if love.keyboard.isDown('z') then
        Player.shoot(dt)
    end

    -- Bomb
    if love.keyboard.isDown('x') and not Player.bombActive and Player.bombs > 0 then
        Player.useBomb()
    end

    Player.shootCooldown = math.max(0, Player.shootCooldown - dt)
end

function Player.shoot(dt)
    if Player.shootCooldown > 0 then return end

    local char = characters[Player.character]
    Player.shootCooldown = 0.08

    if char.shotType == "homing" then
        -- Reimu's homing shots
        Bullets.addPlayerBullet(Player.x - 10, Player.y, 0, -char.shotSpeed, char.shotDamage, "homing")
        Bullets.addPlayerBullet(Player.x + 10, Player.y, 0, -char.shotSpeed, char.shotDamage, "homing")
    elseif char.shotType == "laser" then
        -- Marisa's straight lasers
        Bullets.addPlayerBullet(Player.x, Player.y, 0, -char.shotSpeed, char.shotDamage, "laser")
        Bullets.addPlayerBullet(Player.x - 15, Player.y, 0, -char.shotSpeed, char.shotDamage * 0.8, "laser")
        Bullets.addPlayerBullet(Player.x + 15, Player.y, 0, -char.shotSpeed, char.shotDamage * 0.8, "laser")
    end
end

function Player.useBomb()
    Player.bombs = Player.bombs - 1
    Player.bombActive = true
    Player.bombTime = characters[Player.character].bombDuration
    Player.invincible = true
    Player.invincibleTime = characters[Player.character].bombDuration

    -- Clear all enemy bullets
    Bullets.clearEnemyBullets()

    -- Damage all enemies and bosses
    for _, enemy in ipairs(Enemies.list) do
        enemy.health = 0
    end
    if Bosses.current then
        Bosses.current.health = Bosses.current.health - 200
    end
end

function Player.draw()
    if Player.respawning then
        -- Draw respawn animation
        love.graphics.setColor(1, 1, 1, 0.3)
        love.graphics.circle('fill', Player.x, Player.y, 20 + math.sin(Player.deathTime * 10) * 5)
        return
    end

    local char = characters[Player.character]

    -- Draw bomb effect
    if Player.bombActive then
        local alpha = math.sin(Player.bombTime * 10) * 0.3 + 0.3
        love.graphics.setColor(char.color[1], char.color[2], char.color[3], alpha)
        love.graphics.circle('fill', Player.x, Player.y, 100 * (1 - Player.bombTime / char.bombDuration))
    end

    -- Draw player
    if Player.invincible then
        local alpha = math.floor((Player.invincibleTime * 10) % 2)
        love.graphics.setColor(char.color[1], char.color[2], char.color[3], alpha)
    else
        setColor(char.color)
    end

    love.graphics.circle('fill', Player.x, Player.y, Player.radius)

    -- Draw hitbox when focused
    if love.keyboard.isDown('lshift') or love.keyboard.isDown('rshift') then
        love.graphics.setColor(1, 1, 1, 0.8)
        love.graphics.circle('line', Player.x, Player.y, Player.hitboxRadius)
    end
end

function Player.hit()
    if Player.invincible or Player.bombActive or Player.respawning then
        return false
    end

    Player.lives = Player.lives - 1
    Player.power = math.max(1, Player.power - 0.5)

    if Player.lives <= 0 then
        gameState.current = "gameover"
        return true
    end

    -- Respawn sequence
    Player.respawning = true
    Player.deathTime = 0
    Bullets.clearEnemyBullets()

    return true
end

function Player.getCharacterInfo()
    return characters[Player.character]
end
