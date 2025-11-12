## Unit testing best practices

- **Test Behavior, Not Implementation**: Focus tests on what the code does, not how it does it, to reduce brittleness
- **Clear Test Names**: Use descriptive names that explain what's being tested and the expected outcome
- **Independent Tests**: Each test should run independently without relying on execution order or shared state
- **Test Edge Cases**: Include boundary conditions, empty inputs, null values, and error scenarios
- **Mock External Dependencies**: Isolate units by mocking databases, APIs, file systems, and other external services
- **Fast Execution**: Keep unit tests fast (milliseconds) so developers run them frequently during development
- **One Concept Per Test**: Test one behavior or scenario per test to make failures easy to diagnose
- **Maintain Test Code Quality**: Apply the same code quality standards to tests as to production code
