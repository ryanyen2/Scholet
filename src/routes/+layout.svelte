<script>
	import './styles.css';
</script>

<div class="app">
	<main>
		<slot />
	</main>
</div>

<style>
	.app {
		min-height: 100vh;
	}

	main {
		padding: 1rem;
		/* width: 100%; */
		margin: 0 auto;
		overflow: hidden;
	}
</style>
