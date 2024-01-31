<svelte:head>
  <title>About</title>
  <meta name="description" content="About this visualization" />
</svelte:head>

<div class="text-column">
  <h1>About this Visualization</h1>

  <p>
    This visualization is built with <a href="https://svelte.dev">Svelte</a> and
    <a href="https://d3js.org">D3.js</a>. It presents data from two sources:
    'combined_df' and 'most recent data'.
  </p>

  <ul>
    <li>
      <strong>Data:</strong>
      You can select the data source from a dropdown menu. The data is loaded and
      the visualization is redrawn whenever the data source changes.
      <pre>
publications: Array(20) - 20 top most citated
  title
  year
  cited_by
  url
publications_pubdate: Array(20) - 20 top recent
  title
  year
  cited_by
  url
	  </pre>
    </li>
    <li>
      <strong>Interaction:</strong> You can select an area of the visualization to
      zoom in, and use the home button to reset the zoom and go back to the normal
      view.
    </li>
    <li>
      <strong>Perception:</strong> The visualization is designed to provide a clear
      and concise view of the data. It uses color, size, and position to represent
      different dimensions of the data.
    </li>
  </ul>

  <p>
    To interact with the visualization, simply select an area to zoom in, or use
    the home button to reset the view. The dropdown menu allows you to switch
    between different data sources.
  </p>
</div>
