-- Enemy system

Enemies = {
    list = {},
    spawnTimer = 0
}

function Enemies.init()
    Enemies.list = {}
    Enemies.spawnTimer = 0
end

function Enemies.clear()
    Enemies.list = {}
end

function Enemies.spawn(type, x, y, data)
    local enemy = {
        type = type,
        x = x,
        y = y,
        vx = 0,
        vy = 0,
        health = 10,
        maxHealth = 10,
        radius = 8,
        color = {0.8, 0.3, 0.8},
        score = 100,
        shootTimer = 0,
        shootInterval = 1.5,
        lifetime = 0,
        data = data or {}
    }

    if type == "fairy" then
        enemy.health = 5
        enemy.maxHealth = 5
        enemy.radius = 6
        enemy.color = {0.5, 0.8, 1}
        enemy.score = 50
        enemy.shootInterval = 2
    elseif type == "fairy_strong" then
        enemy.health = 15
        enemy.maxHealth = 15
        enemy.radius = 8
        enemy.color = {1, 0.5, 0.5}
        enemy.score = 150
        enemy.shootInterval = 1
    elseif type == "ghost" then
        enemy.health = 20
        enemy.maxHealth = 20
        enemy.radius = 10
        enemy.color = {0.8, 0.8, 1}
        enemy.score = 200
        enemy.shootInterval = 1.5
    elseif type == "youkai" then
        enemy.health = 30
        enemy.maxHealth = 30
        enemy.radius = 12
        enemy.color = {1, 0.8, 0.3}
        enemy.score = 300
        enemy.shootInterval = 1
    end

    table.insert(Enemies.list, enemy)
end

function Enemies.update(dt)
    Enemies.spawnTimer = Enemies.spawnTimer + dt

    for i = #Enemies.list, 1, -1 do
        local enemy = Enemies.list[i]
        enemy.lifetime = enemy.lifetime + dt
        enemy.shootTimer = enemy.shootTimer + dt

        -- Update movement based on type
        if enemy.type == "fairy" then
            enemy.vx = math.sin(enemy.lifetime * 2) * 50
            enemy.vy = 30
        elseif enemy.type == "fairy_strong" then
            enemy.vx = math.sin(enemy.lifetime * 3) * 80
            enemy.vy = 20
        elseif enemy.type == "ghost" then
            enemy.vx = math.cos(enemy.lifetime) * 60
            enemy.vy = math.sin(enemy.lifetime * 0.5) * 40
        elseif enemy.type == "youkai" then
            local angle = angleTo(enemy.x, enemy.y, Player.x, Player.y)
            local targetVx = math.cos(angle) * 40
            local targetVy = math.sin(angle) * 40
            enemy.vx = lerp(enemy.vx, targetVx, dt * 2)
            enemy.vy = lerp(enemy.vy, targetVy, dt * 2)
        end

        enemy.x = enemy.x + enemy.vx * dt
        enemy.y = enemy.y + enemy.vy * dt

        -- Shooting
        if enemy.shootTimer >= enemy.shootInterval then
            Enemies.shoot(enemy)
            enemy.shootTimer = 0
        end

        -- Remove if out of bounds
        if enemy.y > GAME_BOTTOM + 50 or enemy.y < GAME_TOP - 50 or
           enemy.x < GAME_LEFT - 50 or enemy.x > GAME_RIGHT + 50 then
            table.remove(Enemies.list, i)
        end
    end
end

function Enemies.shoot(enemy)
    if enemy.type == "fairy" then
        Bullets.patterns.aimed(enemy.x, enemy.y, Player.x, Player.y, 3, 100, 0.2, {0.5, 0.8, 1})
    elseif enemy.type == "fairy_strong" then
        Bullets.patterns.circle(enemy.x, enemy.y, 8, 80, {1, 0.5, 0.5})
    elseif enemy.type == "ghost" then
        Bullets.patterns.aimed(enemy.x, enemy.y, Player.x, Player.y, 5, 120, 0.15, {0.8, 0.8, 1}, "kunai")
    elseif enemy.type == "youkai" then
        Bullets.patterns.spiral(enemy.x, enemy.y, 5, 100, enemy.lifetime * 2, {1, 0.8, 0.3}, "star")
    end
end

function Enemies.draw()
    for _, enemy in ipairs(Enemies.list) do
        -- Draw enemy
        setColor(enemy.color)
        love.graphics.circle('fill', enemy.x, enemy.y, enemy.radius)

        -- Draw health bar
        love.graphics.setColor(0, 0, 0, 0.5)
        love.graphics.rectangle('fill', enemy.x - 10, enemy.y - enemy.radius - 8, 20, 3)
        love.graphics.setColor(0.3, 1, 0.3)
        local healthPercent = enemy.health / enemy.maxHealth
        love.graphics.rectangle('fill', enemy.x - 10, enemy.y - enemy.radius - 8, 20 * healthPercent, 3)
    end
end

function Enemies.destroy(index)
    local enemy = Enemies.list[index]
    -- Create particle effect
    for i = 1, 10 do
        local angle = math.random() * math.pi * 2
        local speed = 50 + math.random() * 100
        Particles.add(enemy.x, enemy.y, math.cos(angle) * speed, math.sin(angle) * speed, enemy.color, 0.5)
    end
    table.remove(Enemies.list, index)
end
