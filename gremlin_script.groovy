mgmt = graph.openManagement();
try {
    if (!mgmt.containsPropertyKey('external_urls')) {
        urlProp = mgmt.makePropertyKey('external_urls')
                    .dataType(String.class)
                    .cardinality(Cardinality.LIST)
                    .make();
    }
    mgmt.commit();
} catch (Exception e) {
    mgmt.rollback();
    throw e;
}
