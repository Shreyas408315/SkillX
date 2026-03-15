require('dotenv').config();
const express = require('express');
const cors = require('cors');
const mongoose = require('mongoose');
const jwt = require('jsonwebtoken');
const AWS = require('aws-sdk');
const User = require('./models/User');

const app = express();
const PORT = process.env.PORT || 5000;

// JWT Secret
const JWT_SECRET = process.env.JWT_SECRET || 'your_fallback_super_secret_jwt_key_123';

// Configure AWS SDK
AWS.config.update({
    region: process.env.AWS_REGION || 'us-east-1',
    accessKeyId: process.env.AWS_ACCESS_KEY_ID,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY
});
// Example: const s3 = new AWS.S3();

// Middleware
app.use(cors());
app.use(express.json());

const { MongoMemoryServer } = require('mongodb-memory-server');

// MongoDB Connection
// Spinning up an In-Memory MongoDB server since MongoDB isn't installed locally
async function connectDB() {
    try {
        const mongoServer = await MongoMemoryServer.create();
        const mongoUri = mongoServer.getUri();

        await mongoose.connect(mongoUri);
        console.log(`✅ Connected to In-Memory MongoDB Server Successfully`);
        console.log(`⚠️ Note: Data will be reset when the server restarts since it is stored in memory.`);
    } catch (err) {
        console.error('❌ MongoDB connection error:', err);
        process.exit(1);
    }
}

// Connect to DB and start server
connectDB().then(() => {
    // Start Server (only after DB is connected)
    app.listen(PORT, () => {
        console.log(`Backend Server is running on http://localhost:${PORT}`);
    });
}).catch((err) => {
    console.error('Failed to start server:', err);
    process.exit(1);
});


// ==========================================
// Authentication Routes
// ==========================================

// Register Route (New implementation)
app.post('/api/register', async (req, res) => {
    try {
        const { name, email, password, role } = req.body;

        // Validation: Check for required fields
        if (!name || !email || !password) {
            return res.status(400).json({ 
                success: false, 
                message: 'Please provide name, email, and password.' 
            });
        }

        // Validation: Check email format
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            return res.status(400).json({ 
                success: false, 
                message: 'Please provide a valid email address.' 
            });
        }

        // Validation: Check password length
        if (password.length < 6) {
            return res.status(400).json({ 
                success: false, 
                message: 'Password must be at least 6 characters long.' 
            });
        }

        // Check if user already exists
        const existingUser = await User.findOne({ email: email.toLowerCase() });
        if (existingUser) {
            return res.status(400).json({ success: false, message: 'User with this email already exists.' });
        }

        // Create new user (In a real app, hash password here!)
        const newUser = new User({
            name: name.trim(),
            email: email.toLowerCase(),
            password,
            role: role || 'user'
        });

        await newUser.save();

        // Generate JWT Token
        const token = jwt.sign(
            { id: newUser._id, role: newUser.role },
            JWT_SECRET,
            { expiresIn: '24h' }
        );

        res.status(201).json({
            success: true,
            message: 'User registered successfully!',
            token,
            user: {
                id: newUser._id,
                name: newUser.name,
                email: newUser.email,
                role: newUser.role
            }
        });

    } catch (error) {
        console.error('Registration Error:', error);
        
        // Specific error handling for Mongoose validation errors
        if (error.name === 'ValidationError') {
            const messages = Object.values(error.errors).map(err => err.message);
            return res.status(400).json({ 
                success: false, 
                message: 'Validation error: ' + messages.join(', ') 
            });
        }
        
        // Duplicate key error
        if (error.code === 11000) {
            return res.status(400).json({ 
                success: false, 
                message: 'Email already registered.' 
            });
        }

        res.status(500).json({ 
            success: false, 
            message: 'Server error during registration: ' + error.message 
        });
    }
});


// Login Route (Updated to use MongoDB)
app.post('/api/login', async (req, res) => {
    try {
        const { email, password, role } = req.body;

        // Validation: Check for required fields
        if (!email || !password) {
            return res.status(400).json({
                success: false,
                message: 'Please provide email and password.'
            });
        }

        // Simulate slight delay for authenticating effect
        await new Promise(resolve => setTimeout(resolve, 800));

        // Find user in MongoDB
        const user = await User.findOne({ email: email.toLowerCase() });

        // Check if user exists and password matches
        if (user && user.password === password && (!role || user.role === role)) {
            // Generate JWT Token
            const token = jwt.sign(
                { id: user._id, role: user.role },
                JWT_SECRET,
                { expiresIn: '24h' }
            );

            // Successful login
            res.status(200).json({
                success: true,
                message: 'Login successful',
                token,
                user: {
                    id: user._id,
                    name: user.name,
                    email: user.email,
                    role: user.role
                }
            });
        } else {
            // Failed login
            res.status(401).json({
                success: false,
                message: 'Invalid email, password, or role.'
            });
        }
    } catch (error) {
        console.error('Login Error:', error);
        res.status(500).json({ 
            success: false, 
            message: 'Server error during login: ' + error.message 
        });
    }
});

// Default route to test if server is up
app.get('/', (req, res) => {
    res.send('ElevatePath API is running with MongoDB, JWT, and AWS SDK attached.');
});

// Middleware to verify JWT Token (Use this to protect routes)
const verifyToken = (req, res, next) => {
    const token = req.headers['authorization']?.split(' ')[1]; // Bearer <token>

    if (!token) {
        return res.status(403).json({ success: false, message: 'A token is required for authentication' });
    }

    try {
        const decoded = jwt.verify(token, JWT_SECRET);
        req.user = decoded;
    } catch (err) {
        return res.status(401).json({ success: false, message: 'Invalid Token' });
    }
    return next();
};
