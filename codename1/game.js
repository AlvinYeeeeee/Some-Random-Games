// Game canvas setup
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const scoreElement = document.getElementById('score');
const gameOverElement = document.getElementById('gameOver');

// Game constants
const GRAVITY = 0.5;
const JUMP_POWER = 0.7;
const MAX_JUMP_HOLD = 30; // Maximum frames player can hold jump
const JUMP_FORWARD_SPEED = 4; // Speed to move forward when jumping
const PLATFORM_WIDTH = 100;
const PLATFORM_HEIGHT = 20;
const PLATFORM_GAP_MIN = 50;  // Minimum gap between platforms
const PLATFORM_GAP_MAX = 200; // Maximum gap between platforms
const PLATFORM_HEIGHT_VARIATION = 60; // How much platforms can vary in height

// Game state
let score = 0;
let topScore = 0; // Track the top score
let isGameOver = false;
let isJumping = false;
let jumpHoldTime = 0;
let cameraOffset = 0;
let platformsReached = []; // Array to track which platforms player has reached
let newBestScore = false; // Flag to track if player achieved a new best score

// Player object
const player = {
    x: 100,
    y: 300,
    width: 30,
    height: 30,
    velocityX: 0, // No longer has a constant velocity
    velocityY: 0,
    isOnPlatform: false,
    currentPlatformId: null, // Track which platform player is on
    color: '#3498db'
};

// Platforms array
let platforms = [];
let platformIdCounter = 0; // Unique ID for each platform

// Game initialization
function init() {
    // Reset game state
    score = 0;
    scoreElement.textContent = 'Score: 0';
    isGameOver = false;
    gameOverElement.style.display = 'none';
    jumpHoldTime = 0;
    isJumping = false;
    cameraOffset = 0;
    platformsReached = [];
    platformIdCounter = 0;
    newBestScore = false;
    
    // Create initial platforms
    platforms = [];
    let platformX = 0;
    
    // Create initial platform under player
    platforms.push({
        id: platformIdCounter++,
        x: platformX,
        y: 400,
        width: PLATFORM_WIDTH * 2, // First platform is wider
        height: PLATFORM_HEIGHT
    });
    
    // Reset player and ensure player starts on the first platform
    player.x = 100;
    player.y = 400 - player.height; // Position player directly on first platform
    player.velocityX = 0; // Player doesn't move automatically
    player.velocityY = 0;
    player.isOnPlatform = true;
    player.currentPlatformId = 0;
    
    // Add first platform to reached platforms
    platformsReached.push(0);
    
    // Generate a few more platforms ahead
    platformX += PLATFORM_WIDTH * 2 + getRandomGap();
    for (let i = 0; i < 10; i++) {
        const platformY = getRandomHeight(platforms[platforms.length - 1].y);
        platforms.push({
            id: platformIdCounter++,
            x: platformX,
            y: platformY,
            width: PLATFORM_WIDTH,
            height: PLATFORM_HEIGHT
        });
        platformX += PLATFORM_WIDTH + getRandomGap();
    }
    
    // Start the game loop
    gameLoop();
}

// Get random gap between platforms
function getRandomGap() {
    return Math.random() * (PLATFORM_GAP_MAX - PLATFORM_GAP_MIN) + PLATFORM_GAP_MIN;
}

// Get random height for next platform (with constraints to ensure it's reachable)
function getRandomHeight(previousHeight) {
    // Calculate the maximum height the player can reach
    const maxJumpHeight = (MAX_JUMP_HOLD * JUMP_POWER) * 4; 
    
    let minHeight = previousHeight - PLATFORM_HEIGHT_VARIATION;
    let maxHeight = previousHeight + PLATFORM_HEIGHT_VARIATION;
    
    // Ensure the height is within canvas bounds
    minHeight = Math.max(100, minHeight);
    maxHeight = Math.min(canvas.height - 100, maxHeight);
    
    // Ensure the height difference is within the player's jumping capability
    maxHeight = Math.min(maxHeight, previousHeight + maxJumpHeight);
    
    return Math.random() * (maxHeight - minHeight) + minHeight;
}

// Main game loop
function gameLoop() {
    if (isGameOver) return;
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Update player position
    updatePlayer();
    
    // Check for platform collisions
    checkPlatformCollisions();
    
    // Generate new platforms as needed
    generatePlatforms();
    
    // Remove platforms that are off-screen
    removeOffscreenPlatforms();
    
    // Draw game objects
    drawGame();
    
    // Draw hitboxes for debugging
    drawDebugInfo();
    
    // Check game over condition
    if (player.y > canvas.height) {
        gameOver();
        return;
    }
    
    // Update score display
    scoreElement.textContent = 'Score: ' + score;
    
    // Continue game loop
    requestAnimationFrame(gameLoop);
}

// Draw debug information
function drawDebugInfo() {
    // Draw player hitbox
    ctx.strokeStyle = 'red';
    ctx.lineWidth = 1;
    ctx.strokeRect(
        player.x - cameraOffset,
        player.y,
        player.width,
        player.height
    );
    
    // Draw platform hitboxes
    ctx.strokeStyle = 'yellow';
    for (const platform of platforms) {
        ctx.strokeRect(
            platform.x - cameraOffset,
            platform.y,
            platform.width,
            platform.height
        );
    }
    
    // Show player status
    ctx.fillStyle = 'white';
    ctx.font = '10px Arial';
    ctx.fillText(`On Platform: ${player.isOnPlatform ? 'Yes (ID: ' + player.currentPlatformId + ')' : 'No'}`, 10, 20);
    ctx.fillText(`Position: (${Math.floor(player.x)}, ${Math.floor(player.y)})`, 10, 35);
    ctx.fillText(`Velocity: (${player.velocityX.toFixed(1)}, ${player.velocityY.toFixed(1)})`, 10, 50);
    ctx.fillText(`Platforms Reached: ${platformsReached.length}`, 10, 65);
    
    // Show top score
    ctx.fillText(`Top Score: ${topScore}`, 10, 80);
}

// Update player position
function updatePlayer() {
    // Apply gravity
    player.velocityY += GRAVITY;
    
    // Update position
    player.x += player.velocityX;
    player.y += player.velocityY;
    
    // Update camera offset to keep player in view
    cameraOffset = player.x - 100;
    
    // When player lands on a platform, stop horizontal movement
    if (player.isOnPlatform && !isJumping) {
        player.velocityX = 0;
    }
}

// Check for platform collisions
function checkPlatformCollisions() {
    // Reset platform status
    player.isOnPlatform = false;
    player.currentPlatformId = null;
    
    for (const platform of platforms) {
        // Only check if player is falling
        if (player.velocityY >= 0) {
            // Check if player's feet are at platform level
            const playerBottom = player.y + player.height;
            const platformTop = platform.y;
            
            // Check if player is within platform width
            const playerLeft = player.x;
            const playerRight = player.x + player.width;
            const platformLeft = platform.x;
            const platformRight = platform.x + platform.width;
            
            // More precise collision detection
            if (playerRight > platformLeft && 
                playerLeft < platformRight &&
                playerBottom >= platformTop && 
                playerBottom - player.velocityY <= platformTop + 5) { // Small tolerance
                
                // Place player on top of platform
                player.y = platform.y - player.height;
                player.velocityY = 0;
                player.isOnPlatform = true;
                player.velocityX = 0; // Stop horizontal movement when landing
                player.currentPlatformId = platform.id;
                
                // Check if this is a new platform
                if (!platformsReached.includes(platform.id)) {
                    platformsReached.push(platform.id);
                    score = platformsReached.length - 1; // Subtract 1 to not count starting platform
                }
                
                break;
            }
        }
    }
}

// Generate new platforms as player progresses
function generatePlatforms() {
    const rightmostPlatform = platforms[platforms.length - 1];
    const visibleRight = cameraOffset + canvas.width;
    
    // If the rightmost platform is getting close to the edge of the screen, add more
    if (rightmostPlatform.x + rightmostPlatform.width < visibleRight + 500) {
        const newPlatformX = rightmostPlatform.x + rightmostPlatform.width + getRandomGap();
        const newPlatformY = getRandomHeight(rightmostPlatform.y);
        
        platforms.push({
            id: platformIdCounter++,
            x: newPlatformX,
            y: newPlatformY,
            width: PLATFORM_WIDTH,
            height: PLATFORM_HEIGHT
        });
    }
}

// Remove platforms that are off-screen to the left
function removeOffscreenPlatforms() {
    while (platforms.length > 0 && platforms[0].x + platforms[0].width < cameraOffset - 100) {
        platforms.shift();
    }
}

// Draw game objects
function drawGame() {
    // Draw platforms
    for (const platform of platforms) {
        // Highlight platforms that have been reached
        if (platformsReached.includes(platform.id)) {
            ctx.fillStyle = '#2ecc71'; // Brighter green for reached platforms
        } else {
            ctx.fillStyle = '#27ae60'; // Regular green for unreached platforms
        }
        
        ctx.fillRect(
            platform.x - cameraOffset, 
            platform.y, 
            platform.width, 
            platform.height
        );
    }
    
    // Draw player
    ctx.fillStyle = player.color;
    ctx.fillRect(
        player.x - cameraOffset, 
        player.y, 
        player.width, 
        player.height
    );
}

// Game over function
function gameOver() {
    isGameOver = true;
    
    // Check if player beat the top score
    if (score > topScore) {
        topScore = score;
        newBestScore = true;
    }
    
    // Update game over message with current and top scores
    let gameOverMessage = `Game Over!<br>Score: ${score}<br>Top Score: ${topScore}`;
    
    // Add a message if player got a new best score
    if (newBestScore) {
        gameOverMessage += `<br><span style="color: gold; font-weight: bold;">NEW BEST SCORE!</span>`;
    }
    
    gameOverMessage += `<br>Press Space to Restart`;
    
    // Update game over element with the new message
    gameOverElement.innerHTML = gameOverMessage;
    gameOverElement.style.display = 'block';
}

// Handle keyboard input
document.addEventListener('keydown', function(event) {
    if (event.code === 'Space') {
        // If game is over, restart the game
        if (isGameOver) {
            init();
            return;
        }
        
        // If player is on a platform, initiate jump
        if (player.isOnPlatform && !isJumping) {
            isJumping = true;
            jumpHoldTime = 0;
            player.velocityX = JUMP_FORWARD_SPEED; // Start moving forward when jumping
        }
    }
});

document.addEventListener('keyup', function(event) {
    if (event.code === 'Space') {
        isJumping = false;
    }
});

// Game update function (called every frame)
function gameUpdate() {
    // Handle jump mechanics
    if (isJumping) {
        if (jumpHoldTime < MAX_JUMP_HOLD) {
            player.velocityY -= JUMP_POWER;
            jumpHoldTime++;
        } else {
            isJumping = false;
        }
    }
}

// Add gameUpdate to the animation loop
const originalGameLoop = gameLoop;
gameLoop = function() {
    gameUpdate();
    originalGameLoop();
};

// Start the game
init(); 