import { GoogleGenerativeAI } from '@google/generative-ai'

if (!process.env.GEMINI_API_KEY) {
    throw new Error('GEMINI_API_KEY environment variable is required')
}

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY)

export function getGeminiModel() {
    return genAI.getGenerativeModel({
        model: 'gemini-1.5-pro-latest',
        generationConfig: {
            temperature: 0.7, // Balance créativité et précision
            topP: 0.95,
            topK: 40,
            maxOutputTokens: 8192,
        },
    })
}

export async function generateContent(prompt: string) {
    const model = getGeminiModel()

    const result = await model.generateContent(prompt)
    const response = result.response

    return response.text()
}
