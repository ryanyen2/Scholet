<script>
  import LatentSpace from "./LatentSpace.svelte";

  let apiKey = "";
  let isSubmitted = false;

  async function submitApiKey() {
    const response = await fetch("http://localhost:8000/apikey", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ key: apiKey }),
    });

    if (response.ok) {
      isSubmitted = true;
    }
  }
</script>

<svelte:head>
  <title>Home</title>
  <meta name="description" content="AI Institute in Waterloo" />
</svelte:head>

<section>
  {#if !isSubmitted}
    <form class="api-form" on:submit|preventDefault={submitApiKey}>
      <label for="apiKey">Enter your OpenAI API key:</label>
      <input
        type="password"
        id="apiKey"
        bind:value={apiKey}
        placeholder="sk-..."
        required
      />
      <button type="submit">Submit</button>
    </form>
  {/if}

  <LatentSpace />
</section>

<style>

  .api-form {
    display: flex;
    flex-direction: row;
    padding: 5px;
  }

  .api-form label {
    font-size: 16px;
    font-weight: bold;
    align-content: center;
    margin-right: 10px;
  }

  .api-form input {
    padding: 10px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 16px;
  }

  .api-form button {
/* text button like */
    padding: 10px;
    margin-left: 10px;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 16px;
    cursor: pointer;
    background-color: inherit;
  }

  .api-form button:hover {
    background-color: #f0f4f8;
  }
</style>
