import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const rootEnvPath = path.resolve(__dirname, '../../.env');
dotenv.config({ path: rootEnvPath });
const backendEnvPath = path.resolve(__dirname, '../.env');
dotenv.config({ path: backendEnvPath, override: true });

import { getFirestoreClient } from '../services/firebaseAdmin.js';
import { analyzeSentiment } from '../services/sentimentAnalysis.js';

const POSTS_COLLECTION = 'communityPosts';

async function fixPostSentiments() {
  const firestore = getFirestoreClient();
  
  if (!firestore) {
    console.error('Failed to initialize Firestore');
    return;
  }

  try {
    // Get all posts with neutral sentiment or low confidence
    const postsSnapshot = await firestore.collection(POSTS_COLLECTION)
      .where('sentiment', '==', 'neutral')
      .get();

    console.log(`Found ${postsSnapshot.docs.length} posts with neutral sentiment to reanalyze`);

    for (const doc of postsSnapshot.docs) {
      const post = doc.data();
      console.log(`\nReanalyzing post: "${post.title}"`);
      console.log(`Content: "${post.content}"`);
      
      // Reanalyze sentiment
      const sentimentResult = await analyzeSentiment(post.content);
      console.log(`New sentiment: ${sentimentResult.sentiment} (${sentimentResult.confidence})`);
      
      // Update the post
      await doc.ref.update({
        sentiment: sentimentResult.sentiment,
        sentimentConfidence: sentimentResult.confidence,
        updatedAt: new Date()
      });
      
      console.log(`✅ Updated post: ${doc.id}`);
    }
    
    console.log('\n🎉 Sentiment analysis fix completed!');
  } catch (error) {
    console.error('Error fixing sentiments:', error);
  }
}

// Run the fix
fixPostSentiments();
