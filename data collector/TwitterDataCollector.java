/**
 * INFO 290 FlickOh Project
 * Author: Seongtaek
*/

import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTextArea;
import java.awt.BorderLayout;
import java.awt.event.ActionEvent;
import java.awt.event.ActionListener;
import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.IOException;
import java.io.PrintWriter;
import java.util.Date;

public class TwitterDataCollector {
	
	static final long MILLISECOND = 1000;
	static final String[] labels = {"Run", "Stop"};
	static final String filenameSuffix = "_data.txt";
	
	static JFrame frame;
	static JPanel panel;
	static JButton button;
	static JTextArea textArea;
	static JScrollPane scrollPanel;
	static int state = 1;
	static SampleStreamCollector collector;
	static FileWriter fw;
	static BufferedWriter bw;
	static PrintWriter pw;
	
	public static void main(String[] args) {
		

		try {
			fw = new FileWriter(new Date(System.currentTimeMillis()) + filenameSuffix);
			bw = new BufferedWriter(fw);
			pw = new PrintWriter(bw);
		}
		catch(IOException e) {
					e.printStackTrace();
		}
		
		collector = new SampleStreamCollector(pw);
		collector.collect();
		
		try {
  		pw.close();
  		bw.close();
  		fw.close();
		} catch (IOException e) { e.printStackTrace();}
					
	}
	
	static boolean isRunning() { return state==1 ? true : false; }
	
	static void notifyPausing(int seconds) {
		textArea.append("[" + new Date(System.currentTimeMillis()) + "] : Pausing for " + seconds + " seconds...\n");
	} 
}