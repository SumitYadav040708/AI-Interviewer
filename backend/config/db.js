import mongoose from 'mongoose'

const DEFAULT_MONGO_URI = 'mongodb://127.0.0.1:27017/ai-interviewer'
const RETRY_DELAY_MS = 5000

const connectDB = async () => {
    const mongoUri = process.env.MONGO_URI || DEFAULT_MONGO_URI

    if (!mongoUri.startsWith('mongodb://') && !mongoUri.startsWith('mongodb+srv://')) {
        console.error(
            `Invalid MONGO_URI provided: ${mongoUri}. Please set MONGO_URI to a valid MongoDB connection string starting with "mongodb://" or "mongodb+srv://".`
        )
        return
    }

    try {
        const conn = await mongoose.connect(mongoUri, {
            serverSelectionTimeoutMS: 5000,
            socketTimeoutMS: 45000,
        })
        console.log(`MongoDB Connected: ${conn.connection.host}`)
    } catch (error) {
        const message = error instanceof Error ? error.message : String(error)
        console.error('MongoDB connection failed. Retrying in the background...', message)
        setTimeout(() => {
            connectDB().catch(() => {})
        }, RETRY_DELAY_MS)
    }
}

mongoose.connection.on('connected', () => {
    console.log('MongoDB connection established.')
})

mongoose.connection.on('disconnected', () => {
    console.warn('MongoDB disconnected. Retrying connection...')
    setTimeout(() => {
        connectDB().catch(() => {})
    }, RETRY_DELAY_MS)
})

mongoose.connection.on('error', (error) => {
    console.error('MongoDB connection error:', error)
})

export default connectDB