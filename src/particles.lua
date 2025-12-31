-- Particle effects system

Particles = {
    list = {}
}

function Particles.init()
    Particles.list = {}
end

function Particles.clear()
    Particles.list = {}
end

function Particles.add(x, y, vx, vy, color, lifetime)
    table.insert(Particles.list, {
        x = x,
        y = y,
        vx = vx,
        vy = vy,
        color = color or {1, 1, 1},
        lifetime = lifetime or 0.5,
        maxLifetime = lifetime or 0.5,
        radius = 2
    })
end

function Particles.update(dt)
    for i = #Particles.list, 1, -1 do
        local particle = Particles.list[i]
        particle.lifetime = particle.lifetime - dt

        if particle.lifetime <= 0 then
            table.remove(Particles.list, i)
        else
            particle.x = particle.x + particle.vx * dt
            particle.y = particle.y + particle.vy * dt
            particle.vx = particle.vx * 0.95
            particle.vy = particle.vy * 0.95
        end
    end
end

function Particles.draw()
    for _, particle in ipairs(Particles.list) do
        local alpha = particle.lifetime / particle.maxLifetime
        love.graphics.setColor(particle.color[1], particle.color[2], particle.color[3], alpha)
        love.graphics.circle('fill', particle.x, particle.y, particle.radius)
    end
end
