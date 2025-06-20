# RDF Memory Server Refactoring Todo List

## Phase 1: Foundation - Pure String Functions

### Implement CURIE detection functionality

- [x] Create `src/mcp_rdf_memory/curie.py` module
  - [x] Add module docstring explaining CURIE handling
  - [x] No external dependencies needed

- [x] Implement CURIE pattern detection function
  - [x] Move existing `is_curie` logic from server.py
  - [x] Return False if string contains "://" (full URI)
  - [x] Check for exactly one colon separator
  - [x] Validate prefix part is alphanumeric (with _ or -)
  - [x] Ensure local part is non-empty
  - [x] Add comprehensive pattern documentation

- [x] Create test suite for CURIE detection
  - [x] Test valid CURIE patterns (rdf:type, schema:name)
  - [x] Test invalid patterns (http://example.org, no:colon:twice)
  - [x] Test edge cases (empty parts, special characters)
  - [x] Document expected behavior for each pattern

### Implement basic validation functions

- [x] Create `src/mcp_rdf_memory/validation.py` module
  - [x] Add module docstring explaining validation scope
  - [x] Plan for both pure validation and RDF-specific validation

- [x] Implement prefix validation function
  - [x] Move existing `validate_prefix` logic from server.py
  - [x] Check not empty or whitespace-only
  - [x] Ensure no colons in prefix name
  - [x] Validate alphanumeric with hyphens/underscores
  - [x] Return trimmed prefix
  - [x] Add clear error messages

- [x] Implement basic string validation for RDF nodes
  - [x] Create function to check for empty/whitespace-only strings
  - [x] This will be used by other validation functions
  - [x] Keep it simple and reusable

- [x] Create test suite for basic validation
  - [x] Test prefix validation with valid/invalid inputs
  - [x] Test empty string detection
  - [x] Test whitespace handling
  - [x] Test error message clarity

## Phase 2: RDF Type Converters

### Implement RDF node creation functions

- [ ] Create `src/mcp_rdf_memory/converters.py` module
  - [ ] Add module docstring explaining conversion strategies
  - [ ] Import pyoxigraph types (NamedNode, Literal)
  - [ ] Import ToolError from fastmcp

- [ ] Implement RDF node creation function
  - [ ] Move existing `create_rdf_node` logic from server.py
  - [ ] Try NamedNode first for identifiers
  - [ ] Fall back to Literal for non-URI strings
  - [ ] Handle empty strings appropriately
  - [ ] Document when each type is created

- [ ] Implement graph URI creation function
  - [ ] Move existing `create_graph_uri` logic from server.py
  - [ ] Return None for None or empty string (default graph)
  - [ ] Raise ToolError for whitespace-only names
  - [ ] Create NamedNode with MCP namespace
  - [ ] Trim whitespace from input

- [ ] Create test suite for converters
  - [ ] Test URI strings create NamedNodes
  - [ ] Test plain strings create Literals
  - [ ] Test graph URI generation
  - [ ] Test error cases
  - [ ] Test with pyoxigraph types

## Phase 3: Complete Validation Module

### Extend validation with RDF-specific functions

- [ ] Implement RDF identifier validation function
  - [ ] Move existing `validate_rdf_identifier` logic from server.py
  - [ ] Import and use `is_curie` from curie module
  - [ ] Accept both string and NamedNode inputs
  - [ ] Add explicit CURIE validation using is_curie()
  - [ ] Add URN validation support
  - [ ] Add validation for other schemes (mailto:, file://)
  - [ ] Return string representation

- [ ] Implement RDF node validation function
  - [ ] Move existing `validate_rdf_node` logic from server.py
  - [ ] Use basic string validation from earlier
  - [ ] Accept string, NamedNode, or Literal inputs
  - [ ] Document that any non-empty string is valid
  - [ ] Return string representation

- [ ] Extend test suite for RDF validation
  - [ ] Test identifier validation with URIs, CURIEs, URNs
  - [ ] Test node validation with different input types
  - [ ] Test integration with is_curie function
  - [ ] Test error handling and messages

## Phase 4: CURIE Expansion

### Implement CURIE expansion functionality

- [ ] Extend `curie.py` module with expansion function
  - [ ] Add expansion function after detection function
  - [ ] Keep both functions in same module

- [ ] Implement CURIE expansion function
  - [ ] Move existing `expand_curie` logic from server.py
  - [ ] Use `is_curie()` to check if expansion needed
  - [ ] Accept global and graph-specific prefix dictionaries
  - [ ] Check graph-specific prefixes first (override behavior)
  - [ ] Return original value if no prefix found
  - [ ] Keep as pure function with no external dependencies

- [ ] Extend test suite for CURIE expansion
  - [ ] Test expansion with defined prefixes
  - [ ] Test fallback for undefined prefixes
  - [ ] Test graph-specific override behavior
  - [ ] Test non-CURIE strings pass through
  - [ ] Test with empty prefix dictionaries

## Phase 5: Prefix Management System

### Implement comprehensive prefix management

- [ ] Create `src/mcp_rdf_memory/prefix_manager.py` module
  - [ ] Import validation functions from validation module
  - [ ] Import pyoxigraph NamedNode for URI validation
  - [ ] Design for thread-safe operations if needed

- [ ] Implement PrefixManager initialization
  - [ ] Define standard RDF namespace prefixes in __init__
  - [ ] Initialize empty graph_prefixes dictionary
  - [ ] Set up standard prefixes (rdf, rdfs, owl, etc.)
  - [ ] Allow custom initial prefixes

- [ ] Implement prefix definition functionality
  - [ ] Use `validate_prefix()` from validation module
  - [ ] Validate namespace_uri with NamedNode
  - [ ] Store in appropriate dictionary (global or graph-specific)
  - [ ] Handle prefix updates
  - [ ] Raise ToolError for invalid inputs

- [ ] Implement prefix removal functionality
  - [ ] Remove from global or graph-specific storage
  - [ ] Clean up empty graph prefix dictionaries
  - [ ] Make idempotent (no error if not exists)
  - [ ] Handle cascade scenarios

- [ ] Implement prefix resolution functionality
  - [ ] Get effective prefixes for a graph
  - [ ] Merge global and graph-specific prefixes
  - [ ] Ensure graph-specific override global
  - [ ] Return copies to prevent mutation

- [ ] Implement CURIE expansion helper
  - [ ] Import expand_curie from curie module
  - [ ] Create method that gets effective prefixes
  - [ ] Call expand_curie with correct prefix maps
  - [ ] Provide convenient interface

- [ ] Create test suite for PrefixManager
  - [ ] Test initialization with standard prefixes
  - [ ] Test prefix CRUD operations
  - [ ] Test graph-specific overrides
  - [ ] Test effective prefix resolution
  - [ ] Test CURIE expansion integration

## Phase 6: Result Formatting Module

### Implement consistent result formatting

- [ ] Create `src/mcp_rdf_memory/formatters.py` module
  - [ ] Import types from server (QuadResult, etc.)
  - [ ] Plan for consistent formatting across result types

- [ ] Implement Quad result formatting
  - [ ] Take pyoxigraph Quad object as input
  - [ ] Convert subject, predicate, object to strings
  - [ ] Handle DefaultGraph special case
  - [ ] Extract value from named graphs
  - [ ] Return QuadResult model

- [ ] Implement SPARQL SELECT formatting
  - [ ] Take QuerySolutions from pyoxigraph
  - [ ] Extract variable bindings
  - [ ] Convert each binding to string
  - [ ] Handle None values
  - [ ] Return list of dictionaries

- [ ] Implement SPARQL CONSTRUCT formatting
  - [ ] Take triple iterator from pyoxigraph
  - [ ] Convert each triple to QuadResult
  - [ ] Set graph as "default graph"
  - [ ] Return list of QuadResult

- [ ] Create test suite for formatters
  - [ ] Test with mock pyoxigraph objects
  - [ ] Test each formatter type
  - [ ] Test empty results
  - [ ] Test special characters
  - [ ] Test None handling

## Phase 7: Query Building Module

### Implement query pattern building

- [ ] Create `src/mcp_rdf_memory/query_builder.py` module
  - [ ] Import converters module functions
  - [ ] Import RDF types from pyoxigraph
  - [ ] Design for extensibility

- [ ] Implement PatternQuery class
  - [ ] Store pattern parameters in __init__
  - [ ] Keep both string and node representations
  - [ ] Add validation for pattern components

- [ ] Implement pattern building method
  - [ ] Use converters for node creation
  - [ ] Convert subject/predicate with NamedNode
  - [ ] Convert object with create_rdf_node
  - [ ] Convert graph with create_graph_uri
  - [ ] Handle None values for wildcards

- [ ] Implement query execution method
  - [ ] Accept Store instance
  - [ ] Build pattern nodes
  - [ ] Call store.quads_for_pattern
  - [ ] Return quad iterator
  - [ ] Handle store errors

- [ ] Create test suite for query builder
  - [ ] Test pattern building with various inputs
  - [ ] Test None/wildcard handling
  - [ ] Test with mock Store
  - [ ] Test error propagation
  - [ ] Test all parameter combinations

## Phase 8: Core RDF Service Layer

### Implement service to orchestrate all components

- [ ] Create `src/mcp_rdf_memory/rdf_service.py` module
  - [ ] Import all component modules
  - [ ] Import types from server.py
  - [ ] Design clean interfaces

- [ ] Implement RDFService initialization
  - [ ] Accept StoreManager dependency
  - [ ] Accept PrefixManager dependency
  - [ ] Store both as attributes
  - [ ] Set up any needed state

- [ ] Implement triple addition operation
  - [ ] Import CURIE expansion from PrefixManager
  - [ ] Import node creation from converters
  - [ ] Get effective prefixes for each graph
  - [ ] Expand CURIEs in triple components
  - [ ] Create Quad objects
  - [ ] Use StoreManager for persistence
  - [ ] Handle transactions and errors

- [ ] Implement pattern matching operation
  - [ ] Import QueryBuilder
  - [ ] Import formatters
  - [ ] Build pattern query
  - [ ] Execute with read-only store
  - [ ] Format results
  - [ ] Return formatted results

- [ ] Implement SPARQL execution
  - [ ] Detect query type from results
  - [ ] Use appropriate formatter
  - [ ] Handle different result types
  - [ ] Transform errors appropriately
  - [ ] Return typed results

- [ ] Implement export operations
  - [ ] Use StoreManager for data access
  - [ ] Support full export
  - [ ] Support named graph export
  - [ ] Handle serialization
  - [ ] Return string data

- [ ] Create integration tests for RDFService
  - [ ] Test with real StoreManager
  - [ ] Test with real PrefixManager
  - [ ] Test all operations
  - [ ] Test error scenarios
  - [ ] Test transaction behavior

## Phase 9: Server Refactoring

### Refactor server.py to use new architecture

- [ ] Update imports in server.py
  - [ ] Import RDFService
  - [ ] Import StoreManager
  - [ ] Import PrefixManager
  - [ ] Import validation functions
  - [ ] Remove functions being extracted

- [ ] Refactor server initialization
  - [ ] Create StoreManager with store_path
  - [ ] Create PrefixManager
  - [ ] Create RDFService with dependencies
  - [ ] Remove direct store initialization
  - [ ] Keep backward compatibility

- [ ] Refactor tool implementations
  - [ ] Update rdf_define_prefix to use prefix_manager
  - [ ] Update rdf_add_triples to use service.add_triples
  - [ ] Update rdf_find_triples to use service.find_triples
  - [ ] Update rdf_sparql_query to use service.execute_sparql
  - [ ] Maintain exact same tool interfaces

- [ ] Refactor resource implementations
  - [ ] Update export_all_graphs to use service
  - [ ] Update export_named_graph to use service
  - [ ] Update prefix exports to use prefix_manager
  - [ ] Maintain same resource paths

- [ ] Remove extracted code
  - [ ] Delete all validation functions
  - [ ] Delete CURIE functions
  - [ ] Delete converter functions
  - [ ] Delete inline business logic
  - [ ] Keep only MCP interface code

- [ ] Verify compatibility
  - [ ] Run all existing tests
  - [ ] Ensure no interface changes
  - [ ] Check error messages
  - [ ] Test with MCP clients

## Phase 10: Test Suite Reorganization

### Reorganize tests for new architecture

- [ ] Create directory structure
  - [ ] Create tests/unit/
  - [ ] Create tests/functional/ with subdirectories
  - [ ] Create tests/integration/
  - [ ] Create tests/compliance/
  - [ ] Create tests/system/
  - [ ] Update .gitignore if needed

- [ ] Create unit tests for extracted modules
  - [ ] Write tests/unit/test_curie.py
  - [ ] Write tests/unit/test_validation.py
  - [ ] Write tests/unit/test_converters.py
  - [ ] Write tests/unit/test_prefix_manager.py
  - [ ] Write tests/unit/test_formatters.py
  - [ ] Write tests/unit/test_query_builder.py
  - [ ] Achieve high coverage for each module

- [ ] Migrate existing tests
  - [ ] Move tool tests to functional/
  - [ ] Split integration tests by workflow
  - [ ] Move compliance tests
  - [ ] Move system tests
  - [ ] Update all imports

- [ ] Clean up test code
  - [ ] Remove duplicate test helpers
  - [ ] Consolidate test utilities
  - [ ] Update conftest.py
  - [ ] Fix any broken tests

- [ ] Validate test suite
  - [ ] Run full test suite
  - [ ] Check coverage report
  - [ ] Ensure all tests pass
  - [ ] Add missing test cases

## Phase 11: Final Polish

### Complete documentation and cleanup

- [ ] Add documentation
  - [ ] Write module docstrings
  - [ ] Document all public functions
  - [ ] Add usage examples
  - [ ] Document design decisions
  - [ ] Create architecture overview

- [ ] Add type annotations
  - [ ] Ensure all parameters typed
  - [ ] Add return type annotations
  - [ ] Use proper generic types
  - [ ] Run type checker

- [ ] Code quality
  - [ ] Run linter and fix issues
  - [ ] Run formatter
  - [ ] Remove dead code
  - [ ] Optimize imports
  - [ ] Check for code smells

- [ ] Project documentation
  - [ ] Update README
  - [ ] Document new structure
  - [ ] Add development guide
  - [ ] Update CLAUDE.md if needed

- [ ] Final validation
  - [ ] Full test suite pass
  - [ ] Lint/format clean
  - [ ] Type check pass
  - [ ] Manual testing with Claude Desktop
  - [ ] Performance benchmarks