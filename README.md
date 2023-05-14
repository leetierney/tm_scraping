<h1>Transfermarkt Scraping Script</h1>

<h2>Background</h2>
<p>I spent some time looking at <a href = 'https://github.com/fivethirtyeight/data/tree/master/soccer-spi'>FiveThirtyEight's <s>Soccer</s> <em>Football</em> API</a>,
and had some fun analysing results in a variety of leagues. There were, however, some leagues that were missing. </p>

<p>So, I got thinking: How could I get data for non-supported leagues in a nice, clean format? If you're a football fan, you'll probably be aware of the existence of 
  <a href = 'transfermarkt.com'> Transfermarkt </a>, who are generally my go to for finding historic results, particularly for leagues which aren't well documented on other sites like 
  <a href = 'fbref.com'> FBRef </a>. </p>
  
<p>My specific use case for this was to analyse <a href = 'leagueofireland.ie'> League of Ireland</a> results, and compare them against other leagues across the world. While definitely not the worst one,
  the lack of data available for the League of Ireland is a byproduct of the extremely poor funding the League receives. I haven't been able to put my hands on a handily accessible csv sheet with data,
  for example. I'm open to correction, and will happily accept a link to a nice, clean dataset on our league, but for now, I'll have to pull the data myself. </p>
  
 <p>There are definitely some flaws within the script, and some pieces which need to be improved, but this does the job for now, and offers me the option to at least play around with the data. </p>
 
<h2>Future Improvements</h2>
<ul>
  <li>Tidying up some of the formatting arguments, as they feel inefficient (specifically the referees part). </li>
  <li>Different functions for pulling, formatting, and writing to dataframe. </p>
  <li>Better error handling. </li>
  <li>Writing to a database, to make it handier to query the data. </li>
</ul>
