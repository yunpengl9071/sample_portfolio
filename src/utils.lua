-- Utility functions

function distance(x1, y1, x2, y2)
    return math.sqrt((x2 - x1)^2 + (y2 - y1)^2)
end

function clamp(value, min, max)
    return math.max(min, math.min(max, value))
end

function lerp(a, b, t)
    return a + (b - a) * t
end

function circleCollision(x1, y1, r1, x2, y2, r2)
    return distance(x1, y1, x2, y2) < (r1 + r2)
end

function pointInRect(px, py, rx, ry, rw, rh)
    return px >= rx and px <= rx + rw and py >= ry and py <= ry + rh
end

function angleTo(x1, y1, x2, y2)
    return math.atan2(y2 - y1, x2 - x1)
end

function createColor(r, g, b, a)
    return {r or 1, g or 1, b or 1, a or 1}
end

function setColor(color)
    love.graphics.setColor(color[1], color[2], color[3], color[4] or 1)
end
