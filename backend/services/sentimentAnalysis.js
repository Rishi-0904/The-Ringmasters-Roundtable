import { spawn, exec } from 'child_process';
import path from 'path';
import { fileURLToPath } from 'url';
import { promisify } from 'util';

const execAsync = promisify(exec);
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Path to the sentiment analysis Python script
const SENTIMENT_SCRIPT_PATH = path.join(__dirname, '../sentiment/main.py');
const SENTIMENT_API_URL = 'http://127.0.0.1:5000/predict';

/**
 * Analyze sentiment of text using the trained model (via API, fallback to spawning main.py)
 * @param {string} text - Text to analyze
 * @returns {Promise<{sentiment: string, confidence: number}>}
 */
export const analyzeSentiment = async (text) => {
  const cleanText = text.trim();
  if (!cleanText) {
    return { sentiment: 'neutral', confidence: 0.5 };
  }

  // 1. Try Flask API (Fast Path)
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 2000); // 2s timeout

    const response = await fetch(SENTIMENT_API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text: cleanText }),
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    if (response.ok) {
      const data = await response.json();
      return {
        sentiment: data.result ? data.result.toLowerCase() : 'neutral',
        confidence: data.confidence || 0.8
      };
    }
  } catch (err) {
    // API is not running or failed, fallback to spawning main.py
    console.warn('Sentiment API not running or timed out, falling back to local Python script...');
  }

  // 2. Fallback to Spawn (Slow Path)
  return new Promise((resolve) => {
    const sentimentDir = path.join(__dirname, '../sentiment');
    const escapedText = cleanText.replace(/"/g, '\\"').replace(/\n/g, '\\n');

    const python = spawn('python', [SENTIMENT_SCRIPT_PATH, '--text', escapedText], {
      cwd: sentimentDir,
    });

    let stdout = '';
    let stderr = '';

    python.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    python.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    python.on('close', (code) => {
      if (code !== 0) {
        console.error('Sentiment analysis error - exit code:', code, 'stderr:', stderr);
        return resolve({ sentiment: 'neutral', confidence: 0.5 });
      }

      try {
        const cleanOutput = stdout.trim();
        const result = JSON.parse(cleanOutput);
        
        const sentimentMap = {
          1: 'positive',
          0: 'neutral',
          '-1': 'negative',
          [-1]: 'negative'
        };
        
        resolve({
          sentiment: sentimentMap[result.prediction] || 'neutral',
          confidence: result.confidence || 0.5
        });
      } catch (error) {
        console.error('Error parsing sentiment analysis result:', error);
        resolve({ sentiment: 'neutral', confidence: 0.5 });
      }
    });

    python.on('error', (error) => {
      console.error('Failed to start sentiment analysis:', error);
      resolve({ sentiment: 'neutral', confidence: 0.5 });
    });
  });
};

/**
 * Analyze sentiment of multiple texts in batch
 * @param {string[]} texts - Array of texts to analyze
 * @returns {Promise<Array<{sentiment: string, confidence: number}>>}
 */
export const analyzeSentimentBatch = async (texts) => {
  if (!Array.isArray(texts) || texts.length === 0) {
    return [];
  }

  const cleanTexts = texts.map(t => t.trim());

  // 1. Try Flask API (Fast Path)
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000); // 5s timeout

    const response = await fetch(SENTIMENT_API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ texts: cleanTexts }),
      signal: controller.signal
    });
    clearTimeout(timeoutId);

    if (response.ok) {
      const data = await response.json();
      if (data.results && Array.isArray(data.results)) {
        return data.results.map(res => ({
          sentiment: res.prediction === 1 ? 'positive' : (res.prediction === -1 ? 'negative' : 'neutral'),
          confidence: res.confidence || 0.8
        }));
      }
    }
  } catch (err) {
    console.warn('Sentiment API batch call failed or timed out, falling back to local Python script...');
  }

  // 2. Fallback to Spawn Batch
  const sentimentDir = path.join(__dirname, '../sentiment');
  const escapedBatch = JSON.stringify(cleanTexts).replace(/"/g, '\\"');

  try {
    const result = await execAsync(`python "${SENTIMENT_SCRIPT_PATH}" --batch "${escapedBatch}"`, {
      cwd: sentimentDir,
      timeout: 15000,
    });
    const parsed = JSON.parse(result.stdout.trim());
    return parsed.map(res => {
      const sentimentMap = {
        1: 'positive',
        0: 'neutral',
        '-1': 'negative',
        [-1]: 'negative'
      };
      return {
        sentiment: sentimentMap[res.prediction] || 'neutral',
        confidence: res.confidence || 0.5
      };
    });
  } catch (error) {
    console.error('Batch sentiment analysis error:', error);
    return texts.map(() => ({ sentiment: 'neutral', confidence: 0.5 }));
  }
};

/**
 * Get sentiment statistics for an array of sentiment results
 * @param {Array<{sentiment: string, confidence: number}>} sentiments
 * @returns {Object} Statistics object
 */
export const getSentimentStats = (sentiments) => {
  if (!Array.isArray(sentiments) || sentiments.length === 0) {
    return {
      total: 0,
      positive: 0,
      negative: 0,
      neutral: 0,
      positivePercentage: 0,
      negativePercentage: 0,
      neutralPercentage: 0,
      averageConfidence: 0
    };
  }

  const stats = sentiments.reduce((acc, item) => {
    acc.total++;
    acc[item.sentiment]++;
    acc.totalConfidence += item.confidence;
    return acc;
  }, {
    total: 0,
    positive: 0,
    negative: 0,
    neutral: 0,
    totalConfidence: 0
  });

  return {
    ...stats,
    positivePercentage: Math.round((stats.positive / stats.total) * 100),
    negativePercentage: Math.round((stats.negative / stats.total) * 100),
    neutralPercentage: Math.round((stats.neutral / stats.total) * 100),
    averageConfidence: stats.totalConfidence / stats.total
  };
};
