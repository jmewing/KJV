<?php
/**
 * Insert all KJV series posts into WordPress, IN DATE ORDER, in ONE pass.
 *
 * The whole point: post IDs must ascend in the same order as post_date, so the
 * index order and the archive order agree. Therefore this inserts strictly
 * sequentially, in the order given by the manifest (order 1..N).
 *
 * Run with:  wp eval-file insert-posts.php --allow-root
 *
 * Env:
 *   KJV_CONTENT_DIR   directory holding the per-post json + INDEX.json
 *   KJV_STATUS        publish | future | draft   (default: publish)
 *   KJV_DATE_SHIFT    days to shift every date (integer, default 0)
 *   KJV_DRY_RUN       "1" to verify counts without inserting
 *   KJV_LIMIT         insert only the first N (for a test run)
 */

$dir    = getenv('KJV_CONTENT_DIR') ?: '/root/kjv-content';
$status = getenv('KJV_STATUS') ?: 'publish';
$shift  = (int) (getenv('KJV_DATE_SHIFT') ?: 0);
$dry    = getenv('KJV_DRY_RUN') === '1';
$limit  = (int) (getenv('KJV_LIMIT') ?: 0);

$index = json_decode(file_get_contents($dir . '/INDEX.json'), true);
if (!is_array($index)) { WP_CLI::error("cannot read $dir/INDEX.json"); }
if ($limit) { $index = array_slice($index, 0, $limit); }

WP_CLI::log(sprintf('records: %d   status: %s   shift: %+d days   dry_run: %s',
    count($index), $status, $shift, $dry ? 'yes' : 'no'));

// --- ensure categories exist -------------------------------------------
$cats = [];
foreach ($index as $r) {
    $c = $r['category'] ?? null;
    if (!$c) { continue; }
    if (!isset($cats[$c])) {
        $t = get_term_by('name', $c, 'category');
        if ($t) { $cats[$c] = (int) $t->term_id; }
        elseif (!$dry) {
            $res = wp_insert_term($c, 'category');
            if (is_wp_error($res)) { WP_CLI::error('category ' . $c . ': ' . $res->get_error_message()); }
            $cats[$c] = (int) $res['term_id'];
        }
    }
}
WP_CLI::log('categories: ' . json_encode($cats));

// --- guard: nothing already inserted ------------------------------------
$existing = (int) wp_count_posts('post')->publish + (int) wp_count_posts('post')->future;
if ($existing > 0 && !$dry) {
    $ids = get_posts(['post_type' => 'post', 'numberposts' => 5, 'fields' => 'ids', 'post_status' => 'any']);
    WP_CLI::warning(sprintf('site already has %d published/future posts (sample ids: %s). '
        . 'If those are the WordPress default or a prior partial insert, review before continuing.',
        $existing, implode(',', $ids)));
}

$n = 0; $ids = []; $dates = []; $t0 = microtime(true);
foreach ($index as $i => $r) {
    $f = $dir . '/' . $r['file'];
    if (!file_exists($f)) { WP_CLI::error('missing content file ' . $f); }
    $p = json_decode(file_get_contents($f), true);
    $dt = new DateTime($p['date']);
    if ($shift) { $dt->modify(($shift > 0 ? '+' : '') . $shift . ' days'); }
    $local = $dt->format('Y-m-d H:i:s');
    $gmt   = get_gmt_from_date($local);

    if ($dry) { $n++; $dates[] = $local; continue; }

    $post = [
        'post_title'    => $p['title'],
        'post_content'  => $p['html'],
        'post_name'     => $p['slug'],
        'post_date'     => $local,
        'post_date_gmt' => $gmt,
        'post_status'   => $status,
        'post_type'     => 'post',
        'post_author'   => 1,
    ];
    if (!empty($cats[$p['category']])) { $post['post_category'] = [$cats[$p['category']]]; }

    $id = wp_insert_post($post, true);
    if (is_wp_error($id)) { WP_CLI::error('insert failed at #' . ($i + 1) . ': ' . $id->get_error_message()); }
    $ids[] = $id; $dates[] = $local; $n++;

    if ($n % 100 === 0) {
        WP_CLI::log(sprintf('  inserted %d/%d  (%s)  %.0fs', $n, count($index),
            $local, microtime(true) - $t0));
    }
}
WP_CLI::log(sprintf('%s %d posts in %.0fs', $dry ? 'would insert' : 'inserted',
    $n, microtime(true) - $t0));

// --- VERIFY: id order must match date order -----------------------------
if (!$dry) {
    $inversions = 0; $first = null;
    for ($k = 1; $k < count($dates); $k++) {
        if ($dates[$k] < $dates[$k - 1]) { $inversions++; if ($first === null) $first = $k; }
        if ($ids[$k] < $ids[$k - 1])     { $inversions++; if ($first === null) $first = $k; }
    }
    WP_CLI::log(sprintf('VERIFY date/ID inversions: %d', $inversions));
    WP_CLI::log(sprintf('first id=%d  last id=%d  first date=%s  last date=%s',
        $ids[0], end($ids), $dates[0], end($dates)));
    if ($inversions > 0) { WP_CLI::error('DATE/ID ORDER BROKEN at index ' . $first); }
    WP_CLI::success('insert complete, order verified');
} else {
    WP_CLI::success('dry run complete');
}
