-- Collision detection system

Collision = {}

function Collision.check()
    -- Check player bullets vs enemies
    for i = #Bullets.playerBullets, 1, -1 do
        local bullet = Bullets.playerBullets[i]
        local hit = false

        -- Check against regular enemies
        for j = #Enemies.list, 1, -1 do
            local enemy = Enemies.list[j]
            if circleCollision(bullet.x, bullet.y, bullet.radius, enemy.x, enemy.y, enemy.radius) then
                enemy.health = enemy.health - bullet.damage
                hit = true

                if enemy.health <= 0 then
                    Enemies.destroy(j)
                    gameState.score = gameState.score + enemy.score
                end
                break
            end
        end

        -- Check against boss
        if not hit and Bosses.current and not Bosses.current.defeated then
            local boss = Bosses.current
            if circleCollision(bullet.x, bullet.y, bullet.radius, boss.x, boss.y, boss.radius) then
                boss.health = boss.health - bullet.damage
                hit = true

                if boss.health <= 0 then
                    Bosses.defeatCurrent()
                end
            end
        end

        if hit then
            table.remove(Bullets.playerBullets, i)
        end
    end

    -- Check enemy bullets vs player
    if Player.respawning or Player.invincible or Player.bombActive then
        return
    end

    for i = #Bullets.enemyBullets, 1, -1 do
        local bullet = Bullets.enemyBullets[i]
        if circleCollision(bullet.x, bullet.y, bullet.radius, Player.x, Player.y, Player.hitboxRadius) then
            Player.hit()
            break
        end
    end

    -- Check enemies vs player (collision damage)
    for _, enemy in ipairs(Enemies.list) do
        if circleCollision(enemy.x, enemy.y, enemy.radius, Player.x, Player.y, Player.radius) then
            Player.hit()
            break
        end
    end

    -- Check boss vs player
    if Bosses.current and not Bosses.current.defeated then
        local boss = Bosses.current
        if circleCollision(boss.x, boss.y, boss.radius, Player.x, Player.y, Player.radius) then
            Player.hit()
        end
    end
end
