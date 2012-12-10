/**
 * INFO 290 FlickOh Project
 * Author: Seongtaek and Natth 
*/

import java.io.PrintWriter;

import twitter4j.RateLimitStatusEvent;
import twitter4j.RateLimitStatusListener;
import twitter4j.Status;
import twitter4j.StatusDeletionNotice;
import twitter4j.StatusListener;
import twitter4j.TwitterStream;
import twitter4j.TwitterStreamFactory;
import twitter4j.json.DataObjectFactory;
import twitter4j.conf.ConfigurationBuilder;

public class SampleStreamCollector {
	
	static final long MILLISECOND = 1000;
	
	PrintWriter pw;
	
	SampleStreamCollector(PrintWriter _pw) {
		pw = _pw;
	}
	
	void collect() {
		StatusListener statusListener = new StatusListener() {
			
			public void onStatus(Status status) {
			  String rawJson = DataObjectFactory.getRawJSON(status);
			  pw.println(rawJson+",\n");
			}

			public void onException(Exception e) {}
			
			public void onDeletionNotice(StatusDeletionNotice notice) {}
			
			public void onScrubGeo(long arg0, long arg1) {}

			public void onTrackLimitationNotice(int notice) {}
		};
		
		//	initializing twitter stream
		ConfigurationBuilder cb = new ConfigurationBuilder();
    cb.setDebugEnabled(true)
      .setOAuthConsumerKey("")
      .setOAuthConsumerSecret("")
      .setOAuthAccessToken("")
      .setOAuthAccessTokenSecret("")
      .setJSONStoreEnabled(true);
		TwitterStream twitterStream = new TwitterStreamFactory(cb.build()).getInstance();
		twitterStream.addListener(statusListener);
		
		//	dealing with rate limit - it pauses when rate limit imposed until the next reset
		twitterStream.addRateLimitStatusListener(new RateLimitStatusListener() {

			public void onRateLimitReached(RateLimitStatusEvent event) {
				int secondsUntilReset = event.getRateLimitStatus().getSecondsUntilReset();
				TwitterDataCollector.notifyPausing(secondsUntilReset);
				pauseFor(secondsUntilReset);
				while(!(event.getRateLimitStatus().getRemainingHits()>=event.getRateLimitStatus().getHourlyLimit())) {
					pauseFor(1);
				}
			}

			public void onRateLimitStatus(RateLimitStatusEvent event) {}
		});
		
		twitterStream.sample();
		while(TwitterDataCollector.isRunning()) { pauseFor(1); }
		twitterStream.shutdown();
	}
	
	private void pauseFor(int sec) {
		try { Thread.sleep(sec*MILLISECOND); } catch (InterruptedException e) { e.printStackTrace(); }
	}
}