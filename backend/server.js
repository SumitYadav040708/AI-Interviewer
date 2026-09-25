import express from "express";
import http from "http";
import dotenv from "dotenv";
import cors from "cors";
import { Server } from "socket.io";
import connectDB from "./config/db.js";
import userRoutes from "./routes/userRoutes.js";
import sessionRoutes from "./routes/sessionRoutes.js";
import { notFound, errorHandler } from "./middleware/errorMiddleware.js";

dotenv.config();

connectDB();

const app = express();

const server = http.createServer(app);

const allowedOrigin = [
    'http://localhost:5174',
    'http://localhost:5173',
]

const io = new Server(server, {
    cors: {
        origin: allowedOrigin,
        methods: ['GET', 'POST', 'PUT', 'DELETE',  'OPTIONS'],
        credentials: true,
        allowedHeaders: ['Content-Type', 'Authorization'],
    }
})

app.use(cors({
    origin: allowedOrigin,
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization',"X-Requested-With"],
}))

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

app.set("io", io); //attach socket io instance to express class object ,i.e, set


app.get("/", (req, res) => {
    res.send("API is running");
});

app.use("/api/users", userRoutes);
app.use("/api/sessions", sessionRoutes);

io.on("connection", (socket) => {
    console.log(`A user Connected ${socket.id}`);
    const userId=socket.handshake.query.userId;
    if(userId){

        socket.join(userId);
        console.log(`User ${socket.id} joined room: ${userId}`);
    }

    socket.on("disconnect", () => {
        console.log(`User Disconnected ${socket.id}`);
    });
});

app.use(notFound);
app.use(errorHandler);

const PORT = parseInt(process.env.PORT, 10) || 5001;

const shutDown = () => {
    console.log('\nShutting down backend server...');
    if (server.listening) {
        server.close((err) => {
            if (err) {
                console.error('Error during server shutdown:', err);
                process.exit(1);
            }
            console.log('Backend server stopped.');
            process.exit(0);
        });
    } else {
        console.log('Backend server was not listening. Exiting.');
        process.exit(0);
    }
};

['SIGINT', 'SIGTERM', 'SIGBREAK', 'SIGHUP'].forEach((signal) => {
    process.on(signal, () => {
        console.log(`Received ${signal}, shutting down.`);
        shutDown();
    });
});

process.on('unhandledRejection', (reason) => {
    console.error('Unhandled promise rejection:', reason);
    shutDown();
});

process.on('uncaughtException', (error) => {
    console.error('Uncaught exception:', error);
    shutDown();
});

server.on('error', (error) => {
    if (error.code === 'EADDRINUSE') {
        console.error(`Port ${PORT} is already in use. Stop any running backend process or set PORT to a free port in backend/.env.`);
        process.exit(1);
    }
    console.error('Server error:', error);
    process.exit(1);
});

server.on('listening', () => {
    console.log(`Server running in ${process.env.NODE_ENV} mode on port ${PORT}`);
});

server.listen(PORT);


