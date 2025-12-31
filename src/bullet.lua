-- Bullet system for player and enemy bullets

Bullets = {
    playerBullets = {},
    enemyBullets = {}
}

function Bullets.init()
    Bullets.playerBullets = {}
    Bullets.enemyBullets = {}
end

function Bullets.clear()
    Bullets.playerBullets = {}
    Bullets.enemyBullets = {}
end

function Bullets.clearEnemyBullets()
    Bullets.enemyBullets = {}
end

function Bullets.addPlayerBullet(x, y, vx, vy, damage, type)
    table.insert(Bullets.playerBullets, {
        x = x,
        y = y,
        vx = vx,
        vy = vy,
        damage = damage or 1,
        type = type or "normal",
        radius = 4,
        lifetime = 0,
        target = nil
    })
end

function Bullets.addEnemyBullet(x, y, vx, vy, type, color)
    table.insert(Bullets.enemyBullets, {
        x = x,
        y = y,
        vx = vx,
        vy = vy,
        type = type or "circle",
        color = color or {1, 0.3, 0.3},
        radius = 4,
        lifetime = 0
    })
end

function Bullets.update(dt)
    -- Update player bullets
    for i = #Bullets.playerBullets, 1, -1 do
        local bullet = Bullets.playerBullets[i]
        bullet.lifetime = bullet.lifetime + dt

        -- Homing behavior for Reimu's bullets
        if bullet.type == "homing" then
            local target = Bullets.findNearestTarget(bullet.x, bullet.y)
            if target then
                local angle = angleTo(bullet.x, bullet.y, target.x, target.y)
                local speed = math.sqrt(bullet.vx^2 + bullet.vy^2)
                bullet.vx = math.cos(angle) * speed
                bullet.vy = math.sin(angle) * speed
            end
        end

        bullet.x = bullet.x + bullet.vx * dt
        bullet.y = bullet.y + bullet.vy * dt

        -- Remove if out of bounds
        if bullet.y < GAME_TOP - 20 or bullet.y > GAME_BOTTOM + 20 or
           bullet.x < GAME_LEFT - 20 or bullet.x > GAME_RIGHT + 20 then
            table.remove(Bullets.playerBullets, i)
        end
    end

    -- Update enemy bullets
    for i = #Bullets.enemyBullets, 1, -1 do
        local bullet = Bullets.enemyBullets[i]
        bullet.lifetime = bullet.lifetime + dt

        bullet.x = bullet.x + bullet.vx * dt
        bullet.y = bullet.y + bullet.vy * dt

        -- Remove if out of bounds
        if bullet.y < GAME_TOP - 50 or bullet.y > GAME_BOTTOM + 50 or
           bullet.x < GAME_LEFT - 50 or bullet.x > GAME_RIGHT + 50 then
            table.remove(Bullets.enemyBullets, i)
        end
    end
end

function Bullets.findNearestTarget(x, y)
    local nearest = nil
    local minDist = math.huge

    -- Check enemies
    for _, enemy in ipairs(Enemies.list) do
        local dist = distance(x, y, enemy.x, enemy.y)
        if dist < minDist then
            minDist = dist
            nearest = enemy
        end
    end

    -- Check boss
    if Bosses.current and not Bosses.current.defeated then
        local dist = distance(x, y, Bosses.current.x, Bosses.current.y)
        if dist < minDist then
            minDist = dist
            nearest = Bosses.current
        end
    end

    return nearest
end

function Bullets.draw()
    -- Draw player bullets
    for _, bullet in ipairs(Bullets.playerBullets) do
        if bullet.type == "homing" then
            love.graphics.setColor(1, 0.3, 0.3)
            love.graphics.circle('fill', bullet.x, bullet.y, bullet.radius)
            love.graphics.setColor(1, 1, 1, 0.5)
            love.graphics.circle('fill', bullet.x, bullet.y, bullet.radius * 0.5)
        elseif bullet.type == "laser" then
            love.graphics.setColor(1, 1, 0.5)
            love.graphics.circle('fill', bullet.x, bullet.y, bullet.radius)
            love.graphics.setColor(1, 1, 1, 0.8)
            love.graphics.circle('fill', bullet.x, bullet.y, bullet.radius * 0.3)
        else
            love.graphics.setColor(0.5, 0.5, 1)
            love.graphics.circle('fill', bullet.x, bullet.y, bullet.radius)
        end
    end

    -- Draw enemy bullets
    for _, bullet in ipairs(Bullets.enemyBullets) do
        setColor(bullet.color)

        if bullet.type == "circle" then
            love.graphics.circle('fill', bullet.x, bullet.y, bullet.radius)
        elseif bullet.type == "rice" then
            local angle = math.atan2(bullet.vy, bullet.vx)
            love.graphics.push()
            love.graphics.translate(bullet.x, bullet.y)
            love.graphics.rotate(angle)
            love.graphics.ellipse('fill', 0, 0, bullet.radius * 1.5, bullet.radius)
            love.graphics.pop()
        elseif bullet.type == "kunai" then
            local angle = math.atan2(bullet.vy, bullet.vx)
            love.graphics.push()
            love.graphics.translate(bullet.x, bullet.y)
            love.graphics.rotate(angle)
            love.graphics.polygon('fill', 6, 0, -4, -3, -4, 3)
            love.graphics.pop()
        elseif bullet.type == "star" then
            drawStar(bullet.x, bullet.y, 5, bullet.radius, bullet.radius * 0.4)
        end

        -- Add glow effect
        love.graphics.setColor(bullet.color[1], bullet.color[2], bullet.color[3], 0.3)
        love.graphics.circle('fill', bullet.x, bullet.y, bullet.radius * 1.5)
    end
end

function drawStar(x, y, points, outerRadius, innerRadius)
    local vertices = {}
    for i = 0, points * 2 - 1 do
        local angle = (i * math.pi) / points - math.pi / 2
        local radius = i % 2 == 0 and outerRadius or innerRadius
        table.insert(vertices, x + math.cos(angle) * radius)
        table.insert(vertices, y + math.sin(angle) * radius)
    end
    love.graphics.polygon('fill', vertices)
end

-- Danmaku pattern generators
Bullets.patterns = {}

function Bullets.patterns.circle(x, y, count, speed, color)
    for i = 0, count - 1 do
        local angle = (i / count) * math.pi * 2
        local vx = math.cos(angle) * speed
        local vy = math.sin(angle) * speed
        Bullets.addEnemyBullet(x, y, vx, vy, "circle", color)
    end
end

function Bullets.patterns.spiral(x, y, count, speed, angle, color, type)
    for i = 0, count - 1 do
        local a = angle + (i * 0.3)
        local vx = math.cos(a) * speed
        local vy = math.sin(a) * speed
        Bullets.addEnemyBullet(x, y, vx, vy, type or "circle", color)
    end
end

function Bullets.patterns.aimed(x, y, targetX, targetY, count, speed, spread, color, type)
    local baseAngle = angleTo(x, y, targetX, targetY)
    for i = 0, count - 1 do
        local offset = (i - (count - 1) / 2) * spread
        local angle = baseAngle + offset
        local vx = math.cos(angle) * speed
        local vy = math.sin(angle) * speed
        Bullets.addEnemyBullet(x, y, vx, vy, type or "rice", color)
    end
end

function Bullets.patterns.random(x, y, count, minSpeed, maxSpeed, color)
    for i = 1, count do
        local angle = math.random() * math.pi * 2
        local speed = minSpeed + math.random() * (maxSpeed - minSpeed)
        local vx = math.cos(angle) * speed
        local vy = math.sin(angle) * speed
        Bullets.addEnemyBullet(x, y, vx, vy, "circle", color)
    end
end

function Bullets.patterns.wave(x, y, count, speed, direction, waveWidth, color)
    for i = 0, count - 1 do
        local offset = (i - count / 2) * waveWidth
        local angle = direction
        local vx = math.cos(angle) * speed + math.sin(angle) * offset * 0.3
        local vy = math.sin(angle) * speed - math.cos(angle) * offset * 0.3
        Bullets.addEnemyBullet(x + offset, y, vx, vy, "kunai", color)
    end
end
